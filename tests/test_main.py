import httpx
import pytest
from fastapi.testclient import TestClient

from fastapi_example.main import app, currency_list


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def patch_currency_list(mocker):
    def _patch(mapping):
        return mocker.patch(
            "fastapi_example.main.currency_list", return_value=mapping
        )

    return _patch


class TestCurrencyList:
    def test_returns_full_mapping(self):
        assert currency_list() == {
            "dollar": "USD",
            "euro": "EUR",
            "british sterling": "GBP",
        }


class TestCurrenciesEndpoint:
    def test_delegates_to_currency_list(self, client, patch_currency_list):
        patch_currency_list({"peso": "MXN"})

        response = client.get("/currencies")

        assert response.status_code == 200
        assert response.json() == {"peso": "MXN"}


class TestCurrencySupportedEndpoint:
    @pytest.mark.parametrize(
        "currency_name, currencies, expected_message",
        [
            pytest.param(
                "dollar",
                {"dollar": "USD"},
                "Currency is accepted",
                id="exact-match-accepted",
            ),
            pytest.param(
                "euro",
                {"dollar": "USD", "euro": "EUR"},
                "Currency is accepted",
                id="second-entry-accepted",
            ),
            pytest.param(
                "peso",
                {"dollar": "USD"},
                "Currency not supported",
                id="unknown-rejected",
            ),
            pytest.param(
                "",
                {"dollar": "USD"},
                "Currency not supported",
                id="empty-name-rejected",
            ),
            pytest.param(
                "Dollar",
                {"dollar": "USD"},
                "Currency not supported",
                id="case-sensitive-rejected",
            ),
        ],
    )
    def test_supported_responses(
        self,
        client,
        patch_currency_list,
        currency_name,
        currencies,
        expected_message,
    ):
        patch_currency_list(currencies)

        response = client.post(
            "/currency_supported", json={"currency_name": currency_name}
        )

        assert response.status_code == 200
        assert response.json() == {"message": expected_message}

    def test_missing_field_returns_422(self, client):
        response = client.post("/currency_supported", json={})
        assert response.status_code == 422


@pytest.fixture
def mock_httpx_response(mocker):
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "rates": {"EUR": 0.92, "GBP": 0.78},
        "date": "2026-04-16",
    }
    return response


@pytest.fixture
def mock_httpx_client(mocker, mock_httpx_response):
    async_client = mocker.AsyncMock()
    async_client.get.return_value = mock_httpx_response

    context_manager = mocker.AsyncMock()
    context_manager.__aenter__.return_value = async_client
    context_manager.__aexit__.return_value = None

    mocker.patch(
        "fastapi_example.main.httpx.AsyncClient", return_value=context_manager
    )
    return async_client


class TestExchangeRateEndpoint:
    @pytest.mark.parametrize(
        "query, expected_params",
        [
            pytest.param(
                {"from_currency": "usd", "to_currency": "eur", "amount": 100},
                {"from": "USD", "to": "EUR", "amount": 100.0},
                id="lowercase-input-uppercased",
            ),
            pytest.param(
                {},
                {"from": "USD", "to": "EUR", "amount": 1.0},
                id="defaults-applied",
            ),
            pytest.param(
                {"from_currency": "USD", "to_currency": "GBP"},
                {"from": "USD", "to": "GBP", "amount": 1.0},
                id="target-gbp",
            ),
        ],
    )
    def test_forwards_params_to_frankfurter(
        self, client, mock_httpx_client, query, expected_params
    ):
        client.get("/exchange_rate", params=query)

        mock_httpx_client.get.assert_awaited_once_with(
            "https://api.frankfurter.app/latest", params=expected_params
        )

    def test_successful_conversion_payload(self, client, mock_httpx_client):
        response = client.get(
            "/exchange_rate",
            params={"from_currency": "usd", "to_currency": "eur", "amount": 100},
        )

        assert response.status_code == 200
        assert response.json() == {
            "from": "USD",
            "to": "EUR",
            "amount": 100.0,
            "converted_amount": 0.92,
            "rate": 0.0092,
            "date": "2026-04-16",
        }

    def test_http_status_error_returns_400(
        self, client, mocker, mock_httpx_client, mock_httpx_response
    ):
        mock_httpx_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "bad request",
            request=mocker.Mock(),
            response=mocker.Mock(),
        )

        response = client.get("/exchange_rate")

        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid currency code or API error"}

    def test_generic_exception_returns_500(self, client, mock_httpx_client):
        mock_httpx_client.get.side_effect = ValueError("network boom")

        response = client.get("/exchange_rate")

        assert response.status_code == 500
        assert response.json() == {
            "detail": "Error fetching exchange rate: network boom"
        }

    def test_missing_rate_key_returns_500(
        self, client, mock_httpx_client, mock_httpx_response
    ):
        mock_httpx_response.json.return_value = {"rates": {}, "date": "2026-04-16"}

        response = client.get(
            "/exchange_rate", params={"from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 500
        assert "Error fetching exchange rate" in response.json()["detail"]
