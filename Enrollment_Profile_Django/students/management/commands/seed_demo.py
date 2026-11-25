from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import Classroom, Student


class Command(BaseCommand):
    help = "Add fictional classroom and student examples without overwriting existing records."

    @transaction.atomic
    def handle(self, *args, **options):
        rooms = []
        for year, section in [(2, "A"), (2, "B"), (3, "A")]:
            room, _ = Classroom.objects.get_or_create(
                program="BSIT", year_level=year, section=section,
                school_year="2026-2027", semester="first",
            )
            rooms.append(room)
        records = [
            ("024A-100001", "Aurelia", "Mendoza", "C", "female", 0, "enrolled"),
            ("024A-100002", "Celestine", "Navarro", "R", "female", 0, "enrolled"),
            ("024A-100003", "Seraphina", "Villanueva", "L", "female", 0, "pending"),
            ("024A-100004", "Silas", "Reyes", "M", "male", 0, "enrolled"),
            ("024A-100005", "Isabelle", "Santos", "D", "female", 0, "enrolled"),
            ("024A-100006", "Theo", "Castillo", "A", "male", 1, "enrolled"),
            ("024A-100007", "Amara", "Flores", "B", "female", 1, "pending"),
            ("024A-100008", "Sebastian", "Rivera", "J", "male", 1, "enrolled"),
            ("024A-100009", "Elise", "Torres", "P", "female", 1, "inactive"),
            ("023A-100010", "Lucien", "Garcia", "V", "male", 2, "enrolled"),
            ("023A-100011", "Vivienne", "Cruz", "S", "female", 2, "enrolled"),
            ("023A-100012", "Seth", "Ramos", "T", "male", 2, "enrolled"),
        ]
        created_count = 0
        for index, (sid, first, last, middle, sex, room_index, status) in enumerate(records):
            _, created = Student.objects.get_or_create(student_id=sid, defaults={
                "first_name": first, "last_name": last, "middle_initial": middle,
                "sex": sex, "classroom": rooms[room_index], "status": status,
                "admission_type": "transferee" if index == 6 else "regular",
                "date_of_birth": date(2006 if room_index < 2 else 2005, (index % 12) + 1, 12),
                "place_of_birth": "Lucena City, Quezon",
                "nationality": "Filipino", "civil_status": "single",
                "email": f"{first.lower()}.{last.lower()}@example.com",
                "address": "Sample address, Lucena City, Quezon (fictional)",
                "guardian_name": f"Alex {last} (sample guardian)",
                "guardian_relationship": "Parent",
                "guardian_address": "Sample address, Lucena City, Quezon (fictional)",
                "secondary_school": "Sample Senior High School (fictional)",
                "strand": "Science, Technology, Engineering and Mathematics (STEM)",
                "graduation_year": 2024 if room_index < 2 else 2023,
                "previous_school": "Sample College (fictional)" if index == 6 else "",
            })
            created_count += created
        self.stdout.write(self.style.SUCCESS(f"Added {created_count} fictional students. Existing records were preserved."))
