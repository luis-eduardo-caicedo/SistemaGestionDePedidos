import csv
import os
from datetime import date, datetime
from celery import shared_task
from django.conf import settings
from django.db import connection
from apps.orders.models import ReportRequest


@shared_task
def generate_sales_report(month, year, report_request_id):
    """
    Genera un reporte CSV de ventas para todos los restaurantes, filtrado por mes y año.
    """
    query = """
        SELECT 
            r.id, 
            r.name, 
            COUNT(o.id) AS total_sales, 
            COALESCE(SUM(o.total), 0) AS total_price_sales
        FROM 
            restaurants_restaurant AS r
        INNER JOIN 
            orders_order AS o 
        ON 
            r.id = o.restaurant_id
        WHERE 
            EXTRACT(MONTH FROM o.created_at) = %s
            AND EXTRACT(YEAR FROM o.created_at) = %s
            AND o.status = TRUE
        GROUP BY 
            r.id, r.name
        ORDER BY 
            total_sales DESC;
    """
    params = [month, year]
    
    cursor = connection.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    filename = f"sales_report_{year}_{str(month).zfill(2)}.csv"
    reports_dir = getattr(settings, "REPORTS_DIR", os.path.join(settings.BASE_DIR, "reports"))
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["id", "name", "total_sales", "total_price_sales"])
        for row in rows:
            writer.writerow(row)

    try:
        report_request = ReportRequest.objects.get(pk=report_request_id)
        report_request.status_report = 'completed'
        report_request.report_date = date(year, month, 1)
        report_request.save(update_fields=['status_report', 'report_date'])
    except ReportRequest.DoesNotExist:
        pass

    return {"file_path": filepath, "status_report": "completed", "report_date": f"{year}-{str(month).zfill(2)}-01"}