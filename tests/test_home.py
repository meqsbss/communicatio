def test_home_shows_title(client):
    response = client.get("/")
    assert response.status_code == 200
    assert ".communicatio" in response.content.decode()
