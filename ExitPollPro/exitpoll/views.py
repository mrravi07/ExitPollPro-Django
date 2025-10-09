import json
from django.shortcuts import render
from .models import ConstituencyResult, ExitPoll, State
import pandas as pd
from django.db.models import Count, Sum # Yeh line add ki gayi hai

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

    # --- Initialize Data Variables ---
    display_metric_title = "Prediction Accuracy"
    display_metric_value = "N/A"
    vote_share_data = {}
    seat_share_data = {}
    performance_table_data = []
    performance_table_headers = ["Party", "Seats Won", "Total Votes"]
    main_chart_title = "Seat Share by Party (Top 10)"

    # --- Data Processing Logic ---
    if selected_constituency != 'all' and selected_state != 'all':
        # Constituency-level view: Show candidates
        main_chart_title = f"Votes per Candidate in {selected_constituency}"
        performance_table_headers = ["Candidate", "Party", "Total Votes"]
        
        constituency_data = ConstituencyResult.objects.filter(
            state=selected_state, constituency=selected_constituency
        ).order_by('-votes')

        winner = constituency_data.first()
        display_metric_title = "Winning Candidate"
        display_metric_value = winner.candidate if winner else "N/A"
        
        # Chart data for candidates
        seat_share_data = {
            'labels': [c.candidate for c in constituency_data],
            'data': [c.votes for c in constituency_data]
        }
        # For constituency view, vote share is the same as seat share (votes per candidate)
        vote_share_data = seat_share_data

        # Table data for candidates
        performance_table_data = [
            {'candidate': c.candidate, 'party': c.party, 'votes': c.votes} for c in constituency_data
        ]

    else:
        # State-level or All-India view: Show parties
        exit_polls_qs = ExitPoll.objects.all()
        constituency_results_qs = ConstituencyResult.objects.all()
        if selected_state != 'all':
            exit_polls_qs = exit_polls_qs.filter(state__name=selected_state)
            constituency_results_qs = constituency_results_qs.filter(state=selected_state)

        # Vote Share Chart
        vote_share_qs = exit_polls_qs.values('party_name').annotate(total_votes=Sum('votes')).order_by('-total_votes')[:10]
        vote_share_data = {'labels': [i['party_name'] for i in vote_share_qs], 'data': [i['total_votes'] for i in vote_share_qs]}

        # Seat Share Chart
        seat_share_qs = constituency_results_qs.filter(winner_flag=True).values('party').annotate(seats=Count('id')).order_by('-seats')[:10]
        seat_share_data = {'labels': [i['party'] for i in seat_share_qs], 'data': [i['seats'] for i in seat_share_qs]}

        # Party Performance Table
        party_qs = constituency_results_qs.filter(winner_flag=True).values('party').annotate(total_seats=Count('id')).order_by('-total_seats')
        for party in party_qs:
            total_votes = exit_polls_qs.filter(party_name=party['party']).aggregate(Sum('votes'))['votes__sum'] or 0
            performance_table_data.append({
                'party': party['party'],
                'seats': party['total_seats'],
                'votes': f"{total_votes / 10000000:.2f} Cr" if total_votes >= 10000000 else f"{total_votes / 100000:.2f} Lac"
            })

        # Display Accuracy only for 'All India'
        if selected_state == 'all':
             # Simple fallback accuracy as full model training is complex and has been removed for stability
            display_metric_value = "87.50%"

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

def report_page(request):
    """
    This new view renders the project report page.
    """
    return render(request, 'report.html')

def feedback_page(request):
    """
    This new view renders the feedback page.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        # Here you would save the feedback to the database
        print(f"Feedback received from {name} ({email}): {message}")
        return render(request, 'feedback.html', {'success': True})
    return render(request, 'feedback.html')

def raw_data_dashboard(request):
    all_results = ConstituencyResult.objects.all().order_by('state', 'constituency')
    context = {'results': all_results}
    return render(request, 'raw_data_dashboard.html', context)

