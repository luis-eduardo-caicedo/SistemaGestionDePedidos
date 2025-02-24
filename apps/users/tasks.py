import csv
import os
from celery import shared_task
from apps.users.models import Client


@shared_task
def process_bulk_clients(file_path, user_id):
    processed = 0
    errors = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            rows = list(reader)
            if len(rows) > 20:
                return {"error": "The file contains more than 20 records."}
            for row in rows:
                name = row.get('name')
                email = row.get('email')
                phone = row.get('phone', '')
                if not name or not email:
                    errors.append(f"Missing name or email in row: {row}")
                    continue

                if Client.objects.filter(email=email).exists():
                    errors.append(f"Email {email} already exists.")
                    continue
                Client.objects.create(name=name, email=email, phone=phone, status=True)
                processed += 1
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    return {"processed": processed, "errors": errors}