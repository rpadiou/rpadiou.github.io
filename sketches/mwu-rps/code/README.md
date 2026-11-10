# MWU in rock-paper-scissors

    uv run mwu_rps.py

Runs the simulation (seed fixed), checks every claim made on the page with assertions (KL to Nash increasing for MWU, decreasing for optimistic MWU, average close to Nash, several step sizes and seeds, optimistic MWU still converging at η = 0.3, 0.4 and 0.5, optimistic MWU ahead of plain MWU in 80 head-to-head runs, closed form against a fixed opponent), writes `results.json`, and regenerates `../tweet.png`, `../figure-uniform.png`, `../figure-duel.png`. Takes a few minutes (80 head-to-head runs, long runs for the robustness checks).
