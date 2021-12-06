import plotly.graph_objects as go

# prepare some data
x = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
y = [i**2 for i in x]

# create a new plot
fig = go.Figure(
    layout=dict(
        title="Example Plotly plot",
        yaxis_type="log",
        yaxis_range=[-3, 3],  # Plotly takes ranges differently!
        xaxis_title='sections',
        yaxis_title='particles',
    )
)

# plot some data ('traces' in Plotly)
fig.add_trace(go.Scatter(x=x, y=x, mode='markers', name="y=x", marker=dict(color='royalblue', size=8)))
fig.add_trace(go.Scatter(x=x, y=y, name="y=x^2", line=dict(width=3)))

# show the results
fig.show()
