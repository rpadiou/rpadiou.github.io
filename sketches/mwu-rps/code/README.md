# MWU in rock-paper-scissors

    uv run mwu_rps.py

Runs the simulation (seed fixed), checks every claim made on the page with assertions (KL to Nash increasing for MWU, decreasing for optimistic MWU, average close to Nash, several step sizes and seeds), writes `results.json`, and regenerates `../tweet.png` and `../figure-{light,dark}.png`. Takes about a minute.
