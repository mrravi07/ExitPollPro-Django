import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from exitpoll.models import State, ConstituencyResult, ExitPoll

class Command(BaseCommand):
    help = 'Loads election data from a CSV file into the database.'

    def handle(self, *args, **options):
        self.stdout.write("Starting data import...")
        
        file_path = os.path.join(settings.BASE_DIR, 'datasets', 'india_2019_raw.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found at {file_path}"))
            return
        
        df = pd.read_csv(file_path)

        # --- DATA CLEANING ---
        # Step 1: Remove leading/trailing spaces from column names
        df.columns = df.columns.str.strip()
        # Step 2: Replace line breaks ('\n') with a space in column names
        df.columns = df.columns.str.replace('\n', ' ')
        # --- CLEANING COMPLETE ---

        # Correct column names after cleaning
        STATE_COLUMN = 'STATE'
        PARTY_COLUMN = 'PARTY'
        VOTES_COLUMN = 'TOTAL VOTES'
        WINNER_COLUMN = 'WINNER'
        CONSTITUENCY_COLUMN = 'CONSTITUENCY'
        CANDIDATE_COLUMN = 'NAME'
        
        # Clean the WINNER column to ensure it only has 0s and 1s
        df[WINNER_COLUMN] = pd.to_numeric(df[WINNER_COLUMN], errors='coerce').fillna(0).astype(int)

        state_party_votes = df.groupby([STATE_COLUMN, PARTY_COLUMN]).agg(
            votes=(VOTES_COLUMN, 'sum')
        ).reset_index()

        State.objects.all().delete()
        ExitPoll.objects.all().delete()
        ConstituencyResult.objects.all().delete()

        self.stdout.write("Populating ConstituencyResult model...")
        constituency_results = []
        for _, row in df.iterrows():
            constituency_results.append(
                ConstituencyResult(
                    state=row[STATE_COLUMN],
                    constituency=row[CONSTITUENCY_COLUMN],
                    party=row[PARTY_COLUMN],
                    candidate=row[CANDIDATE_COLUMN],
                    votes=row[VOTES_COLUMN],
                    winner_flag=bool(row[WINNER_COLUMN])
                )
            )
        ConstituencyResult.objects.bulk_create(constituency_results)
        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {len(constituency_results)} constituency results."))

        self.stdout.write("Populating State and ExitPoll models...")
        for _, row in state_party_votes.iterrows():
            state, _ = State.objects.get_or_create(name=row[STATE_COLUMN])
            ExitPoll.objects.create(
                state=state,
                party_name=row[PARTY_COLUMN],
                votes=row['votes']
            )
        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {len(state_party_votes)} aggregated results."))
        
        self.stdout.write(self.style.SUCCESS("Data import complete!"))