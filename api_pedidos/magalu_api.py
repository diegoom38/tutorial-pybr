import os
from http import HTTPStatus
from uuid import UUID

import httpx

from api_pedidos.esquema import Item
from api_pedidos.excecao import (
    FalhaDeComunicacaoError,
    PedidoNaoEncontradoError,
)

# tenant e apikey fixos somente para demonstrações
APIKEY = os.environ.get("APIKEY", "coloque aqui sua apikey")
TENANT_ID = os.environ.get("TENANT_ID", "21fea73c-e244-497a-8540-be0d3c583596")
MAGALU_API_URL = "https://alpha.api.magalu.com"
MAESTRO_SERVICE_URL = f"{MAGALU_API_URL}/maestro/v1"


def _recupera_itens_por_pacote(uuid_do_pedido, uuid_do_pacote):
    response = httpx.get(
        f"{MAESTRO_SERVICE_URL}/orders/{uuid_do_pedido}/packages/"
        f"{uuid_do_pacote}/items",
        headers={"X-Api-Key": APIKEY, "X-Tenant-Id": TENANT_ID},
    )
    response.raise_for_status()
    return [
        Item(
            sku=item["product"]["code"],
            # campos que utilizam a função get são opicionais
            description=item["product"].get("description", ""),
            image_url=item["product"].get("image_url", ""),
            reference=item["product"].get("reference", ""),
            quantity=item["quantity"],
        )
        for item in response.json()
    ]


def recuperar_itens_por_pedido(identificacao_do_pedido: UUID) -> list[Item]:
    try:
        response = httpx.get(
            f"{MAESTRO_SERVICE_URL}/orders/{identificacao_do_pedido}",
            headers={"X-Api-Key": APIKEY, "X-Tenant-Id": TENANT_ID},
        )
        response.raise_for_status()
        pacotes = response.json()["packages"]
        itens = []
        for pacote in pacotes:
            itens.extend(
                _recupera_itens_por_pacote(
                    identificacao_do_pedido, pacote["uuid"]
                )
            )
        return itens
    except httpx.HTTPStatusError as exc:
        # aqui poderiam ser tratados outros erros como autenticação
        if exc.response.status_code == HTTPStatus.NOT_FOUND:
            raise PedidoNaoEncontradoError() from exc
        raise exc
    except httpx.HTTPError as exc:
        raise FalhaDeComunicacaoError() from exc
