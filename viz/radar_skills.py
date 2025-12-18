import plotly.graph_objects as go

def radar_chart(skills: dict):
    labels = list(skills.keys())
    values = list(skills.values())
    # close the loop
    labels += [labels[0]]
    values += [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=labels, fill="toself", name="Target Skills"))
    fig.update_layout(title="Skill Radar (Target Levels)", polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    return fig
