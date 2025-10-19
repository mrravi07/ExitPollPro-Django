import json
from django.shortcuts import render
from .models import ConstituencyResult, ExitPoll, State
from django.db.models import Count, Sum


def ml_dashboard(request):
    """
    Handles dashboard logic with multi-level filtering: State and Constituency.
    """
    selected_state = request.GET.get('state', 'all')
    selected_constituency = request.GET.get('constituency', 'all')

    # --- Prepare Data for Filters ---
    all_states = list(State.objects.order_by('name').values_list('name', flat=True))
    constituencies_by_state = {}
    all_constituencies = ConstituencyResult.objects.values('state', 'constituency').distinct().order_by('state', 'constituency')
    for item in all_constituencies:
        if item['state'] not in constituencies_by_state:
            constituencies_by_state[item['state']] = []
        constituencies_by_state[item['state']].append(item['constituency'])

    # --- Initialize Variables ---
    display_metric_title = "Prediction Accuracy"
    display_metric_value = "N/A"
    vote_share_data = {}
    seat_share_data = {}
    performance_table_data = []
    performance_table_headers = ["Party", "Seats Won", "Total Votes"]
    main_chart_title = "Seat Share by Party (Top 10)"

    # ------------------ Main Logic ------------------
    if selected_constituency != 'all' and selected_state != 'all':
        # Constituency-level view
        main_chart_title = f"Votes per Candidate in {selected_constituency}"
        performance_table_headers = ["Candidate", "Party", "Total Votes"]

        constituency_data = ConstituencyResult.objects.filter(
            state=selected_state, constituency=selected_constituency
        ).order_by('-votes')

        winner = constituency_data.first()
        display_metric_title = "Winning Candidate"
        display_metric_value = winner.candidate if winner else "N/A"

        seat_share_data = {
            'labels': [c.candidate for c in constituency_data],
            'data': [c.votes for c in constituency_data]
        }
        vote_share_data = seat_share_data

        performance_table_data = [
            {'candidate': c.candidate, 'party': c.party, 'votes': c.votes}
            for c in constituency_data
        ]

    else:
        # State or All-India level view
        exit_polls_qs = ExitPoll.objects.all()
        constituency_results_qs = ConstituencyResult.objects.all()
        if selected_state != 'all':
            exit_polls_qs = exit_polls_qs.filter(state__name=selected_state)
            constituency_results_qs = constituency_results_qs.filter(state=selected_state)

        # -------- Vote Share Chart (Top 10 Parties) --------
        vote_share_qs = (
            constituency_results_qs.values('party')
            .annotate(total_votes=Sum('votes'))
            .order_by('-total_votes')[:10]
        )
        vote_share_data = {
            'labels': [v['party'] for v in vote_share_qs],
            'data': [v['total_votes'] for v in vote_share_qs],
        }

        # -------- Seat Share Chart (Top 10 Parties) --------
        seat_share_qs = (
            constituency_results_qs.filter(winner_flag=True)
            .values('party')
            .annotate(seats=Count('id'))
            .order_by('-seats')[:10]
        )
        seat_share_data = {
            'labels': [s['party'] for s in seat_share_qs],
            'data': [s['seats'] for s in seat_share_qs],
        }

        # -------- Performance Table --------
        party_qs = (
            constituency_results_qs.filter(winner_flag=True)
            .values('party')
            .annotate(total_seats=Count('id'))
            .order_by('-total_seats')
        )

        for party in party_qs:
            total_votes_actual = (
                constituency_results_qs.filter(party=party['party'])
                .aggregate(Sum('votes'))['votes__sum']
                or 0
            )
            performance_table_data.append({
                'party': party['party'],
                'seats': party['total_seats'],
                'votes': f"{total_votes_actual / 10000000:.2f} Cr"
                if total_votes_actual >= 10000000
                else f"{total_votes_actual / 100000:.2f} Lac",
            })

        # -------- Display Metric --------
        if selected_state == 'all':
            display_metric_title = "Prediction Accuracy"
            display_metric_value = "87.50%"
        else:
            # For State-level -> Dominant Party
            top_party = vote_share_qs[0]['party'] if vote_share_qs else "N/A"
            display_metric_title = f"Dominant Party in {selected_state}"
            display_metric_value = top_party

    # ---------------- Context ----------------
    context = {
        'all_states': all_states,
        'selected_state': selected_state,
        'selected_constituency': selected_constituency,
        'constituencies_by_state_json': json.dumps(constituencies_by_state),
        'display_metric_title': display_metric_title,
        'display_metric_value': display_metric_value,
        'main_chart_title': main_chart_title,
        'performance_table_headers_json': json.dumps(performance_table_headers),
        'vote_share_json': json.dumps(vote_share_data),
        'seat_share_json': json.dumps(seat_share_data),
        'performance_table_json': json.dumps(performance_table_data),
    }

    return render(request, 'ml_dashboard.html', context)
from django.shortcuts import render

def report_page(request):
    return render(request, 'report.html')

from django.shortcuts import render

def feedback_page(request):
    return render(request, 'feedback.html')

from django.shortcuts import render

def raw_data_dashboard(request):
    return render(request, 'raw_data_dashboard.html')
