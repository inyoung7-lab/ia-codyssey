"""Deterministic facts and record-keeping suggestions, never exercise judgments."""


def build_facts(analysis):
    s = analysis['statistics']
    if not s['record_count']:
        return {key: ['분석할 운동 기록이 없습니다.'] for key in ('summary', 'strength', 'improvement', 'next_workout')}
    summary = [
        f"최근 30일 중 기록된 날은 {s['record_count']}일이며 운동일은 {s['workout_days']}일, 휴식일은 {s['rest_days']}일입니다.",
        f"총 운동시간은 {s['total_minutes']}분이고 기록일 평균은 {s['average_minutes']:g}분입니다.",
        f"운동한 날의 평균 운동시간은 {s['active_day_average_minutes']:g}분입니다.",
        f"최근 7일 총 운동시간은 {s['recent_7_total_minutes']}분이고 이전 7일은 {s['previous_7_total_minutes']}분입니다.",
    ]
    if s['change_minutes'] == 0:
        summary.append('두 기간의 기록된 총 운동시간은 같습니다.')
    else:
        percent = '' if s['change_percent'] is None else f", {abs(s['change_percent']):g}%"
        summary.append(f"최근 7일의 기록된 총 운동시간은 이전 7일보다 {abs(s['change_minutes'])}분{percent} {s['trend']}했습니다.")
    active = [(name, count) for name, count in s['activity_frequency'].items() if count]
    patterns = [f"최근 7일에는 {s['recent_7_record_count']}일의 기록이 있습니다."]
    if active:
        patterns.append('단순 문자열 분류 결과 ' + ', '.join(f'{name} {count}회' for name, count in active) + '가 기록되어 있습니다.')
        maximum = max(count for _, count in active)
        names = ', '.join(name for name, count in active if count == maximum)
        patterns.append(f"가장 많이 분류된 활동은 {names}이며 각각 {maximum}회입니다.")
    patterns += [
        f"분석기간 내 최장 연속 운동은 {s['longest_workout_streak']}일, 최장 연속 휴식은 {s['longest_rest_streak']}일입니다.",
        f"현재 연속 운동 기록은 {s['current_workout_streak']}일이고 연속 휴식 기록은 {s['current_rest_streak']}일입니다.",
    ]
    # State the analysis scope, not absence of information in free-text memos.
    limitations = ['이번 통계는 날짜와 운동시간, 메모의 단순 활동 분류만 사용하므로 운동 강도를 판단하지 않습니다.']
    if s['missing_days']:
        limitations.append(f"분석기간 중 {s['missing_days']}일의 기록이 없어 해당 날짜를 휴식일로 간주하지 않습니다.")
    if s['recent_7_record_count'] != 7 or s['previous_7_record_count'] != 7:
        limitations.append('두 기간에 기록이 없는 날짜가 있어 총 운동시간 비교에 주의가 필요합니다.')
    return {
        'summary': summary, 'strength': patterns, 'improvement': limitations,
        'next_workout': ['다음 기록에서도 날짜와 운동시간을 확인하고 활동 종류를 메모에 구체적으로 남겨 보세요.'],
    }


def rules_feedback(facts):
    return {key: ' '.join(sentences[:2]) for key, sentences in facts.items()}
