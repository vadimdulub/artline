"""Compare source/database instants without treating ISO timezone spelling as data drift."""
from datetime import datetime,timezone
def instant(value):
 t=datetime.fromisoformat(value.replace('Z','+00:00'));assert t.tzinfo is not None,'Timezone required';return t.astimezone(timezone.utc)
def same_instant(a,b):return instant(a)==instant(b)
