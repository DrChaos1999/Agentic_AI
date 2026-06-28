from __future__ import annotations

import argparse

import mlflow
from mlflow import MlflowClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-uri", default="sqlite:///./mlflow.db")
    parser.add_argument("--model-name", default="FactoryLensDefectClassifier")
    parser.add_argument("--version", required=True)
    parser.add_argument("--alias", default="champion")
    args = parser.parse_args()
    mlflow.set_tracking_uri(args.tracking_uri)
    client = MlflowClient()
    client.set_registered_model_alias(args.model_name, args.alias, args.version)
    print(f"Set models:/{args.model_name}@{args.alias} -> version {args.version}")


if __name__ == "__main__":
    main()
