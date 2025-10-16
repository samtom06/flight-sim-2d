
import sys
import flight2d.cli as flight_cli  

DEFAULT_ARGS = [
    "--live",
    "--dt", "0.02",
    "--model", "polar",
    "--pitch-deg", "15",
    "--gamma0-deg", "10",
    "--speed0", "70",
    "--t-max", "60",
]

if __name__ == "__main__":
    
    sys.argv = ["run_sim"] + DEFAULT_ARGS
    flight_cli.main()
