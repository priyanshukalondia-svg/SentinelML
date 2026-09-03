def test_dataset_versions_increment(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        r1 = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("versioning_sample.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )
    with open(sample_csv_path, "rb") as f:
        r2 = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("versioning_sample.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )

    d1, d2 = r1.json(), r2.json()
    assert d1["dataset_id"] == d2["dataset_id"]
    assert d1["version"] != d2["version"]
    assert d1["version"] == "v1.0"
    assert d2["version"] == "v1.1"
