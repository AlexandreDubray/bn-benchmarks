using Logging
using JuMP, Gurobi
using DecisionProgramming

const N = {}
const c_k = {}
const b = 0.03
fortification(k, a) = [c_k[k], 0][a]

@info("Creating the influence diagram.")
diagram = InfluenceDiagram()

add_node!(diagram, ChanceNode("L", [], ["high", "low"]))

for i in 1:N
    add_node!(diagram, ChanceNode("R$i", ["L"], ["high", "low"]))
    add_node!(diagram, DecisionNode("A$i", ["R$i"], ["yes", "no"]))
end

add_node!(diagram, ChanceNode("F", ["L", ["A$i" for i in 1:N]...], ["failure", "success"]))

add_node!(diagram, ValueNode("T", ["F", ["A$i" for i in 1:N]...]))

generate_arcs!(diagram)

X_L = [{}, 0]
X_L[2] = 1.0 - X_L[1]
add_probabilities!(diagram, "L", X_L)

xs = {}
for i in 1:N
	x_R, y_R = xs[i]
    X_R = ProbabilityMatrix(diagram, "R$i")
    X_R["high", "high"] = max(x_R, 1-x_R)
    X_R["high", "low"] = 1 - max(x_R, 1-x_R)
    X_R["low", "low"] = max(y_R, 1-y_R)
    X_R["low", "high"] = 1-max(y_R, 1-y_R)
    add_probabilities!(diagram, "R$i", X_R)
end


X_F = ProbabilityMatrix(diagram, "F")
x_F, y_F = {}
for s in paths([State(2) for i in 1:N])
    denominator = exp(b * sum(fortification(k, a) for (k, a) in enumerate(s)))
    s1 = [s...]
    X_F[1, s1..., 1] = max(x_F, 1-x_F) / denominator
    X_F[1, s..., 2] = 1.0 - X_F[1, s..., 1]
    X_F[2, s..., 1] = min(y_F, 1-y_F) / denominator
    X_F[2, s..., 2] = 1.0 - X_F[2, s..., 1]
end
add_probabilities!(diagram, "F", X_F)


Y_T = UtilityMatrix(diagram, "T")
for s in paths([State(2) for i in 1:N])
    cost = sum(-fortification(k, a) for (k, a) in enumerate(s))
    Y_T[1, s...] = 0 + cost
    Y_T[2, s...] = 100 + cost
end
add_utilities!(diagram, "T", Y_T)

generate_diagram!(diagram, positive_path_utility=true)


model = Model()
z = DecisionVariables(model, diagram)
x_s = PathCompatibilityVariables(model, diagram, z, probability_cut = false)
EV = expected_value(model, diagram, x_s)
@objective(model, Max, EV)

@info("Starting the optimization process.")
optimizer = optimizer_with_attributes(
    () -> Gurobi.Optimizer(Gurobi.Env()),
    "IntFeasTol"      => 1e-9,
)
set_optimizer(model, optimizer)

optimize!(model)
Z = DecisionStrategy(z)
print(Z)
