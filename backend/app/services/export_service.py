import csv
import io
from typing import List
from app.schemas.solver import SolutionEntry

class ExportService:
    @staticmethod
    def to_csv(entries: List[dict]) -> str:
        """
        Convert solution entries to CSV format.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Day', 'Time', 'Course', 'Teacher', 'Room', 'Batch'])
        
        # Rows
        for entry in entries:
            writer.writerow([
                entry.get('day'),
                entry.get('time'),
                entry.get('course_code'),
                entry.get('teacher'),
                entry.get('room'),
                entry.get('batch', 'ALL')
            ])
            
        return output.getvalue()
