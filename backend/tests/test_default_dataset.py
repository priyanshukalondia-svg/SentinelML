def test_load_default_dataset(client):
    response = client.post("/api/v1/datasets/default")

    assert response.status_code == 200
    dataset = response.json()
    assert dataset["dataset_id"] == "sentinelml_default_transactions"
    assert dataset["target_column"] == "fraud"
    assert dataset["row_count"] == 5000
    assert dataset["validation_status"] in ("HEALTHY", "WARNING")