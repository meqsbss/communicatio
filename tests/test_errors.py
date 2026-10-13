def test_unknown_url_returns_404(client):
    assert client.get("/nope/").status_code == 404
