import networkx as nx
import plotly.graph_objects as go

def skill_network_plot(diagnosis_payload, mentor_plan):
    G = nx.Graph()

    # Nodes: skills
    skills = [s.get("skill", "Skill") for s in diagnosis_payload.get("skill_gaps", [])[:10]]
    for sk in skills:
        G.add_node(sk, kind="skill")

    # Nodes: mentors
    recs = mentor_plan.get("recommended_mentors_by_skill", [])
    for r in recs:
        mentor = r.get("recommended_persona", "Mentor")
        skill = r.get("skill", "")
        G.add_node(mentor, kind="mentor")
        if skill:
            G.add_edge(skill, mentor)

    pos = nx.spring_layout(G, seed=42)

    edge_x, edge_y = [], []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x, node_y, node_text = [], [], []
    for n in G.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        node_text.append(n)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", name="links"))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text", text=node_text, textposition="top center", name="nodes"))

    fig.update_layout(title="Skill ↔ Mentor Network", showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig
