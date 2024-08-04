import argparse
from pathlib import Path

from src.server.data_factory import load_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load data with refresh options.")
    parser.add_argument("--refresh_train", type=bool, default=False, help="Refresh train data")
    parser.add_argument("--refresh_test", type=bool, default=False, help="Refresh test data")

    args = parser.parse_args()

    load_data(args.refresh_train, args.refresh_test)
