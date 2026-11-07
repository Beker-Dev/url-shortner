# URL Shortner

The API stores URL shorteners in Apache Cassandra using ScyllaDB's
Python driver (`scylla-driver`), which also supports Apache Cassandra.

## Executar com Docker Compose

Suba o Cassandra 5.0.9, o Redis e a API:

No PowerShell, gere e salve uma chave local no `.env` (ignorado pelo Git)
antes de subir o Compose:

```powershell
[IO.File]::WriteAllText(
  "$PWD\.env",
  "SHORT_CODE_SECRET_KEY=$([Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)))",
  [Text.UTF8Encoding]::new($false)
)
docker compose up --build
```

O Compose aguarda o Cassandra e o Redis ficarem saudáveis, cria o keyspace
`url_shortner` e então inicia a API. O contador Redis é persistido no volume
`redis_data`, e os dados do Cassandra no volume `cassandra_data`. A API fica
disponível em `http://localhost:8000` por padrão. Se a porta 8000 já estiver
ocupada, defina `API_PORT` para outra porta (por exemplo, `API_PORT=8001`).

Para encerrar os containers sem apagar os dados:

```bash
docker compose down
```

## Cassandra configuration

Create the keyspace before starting the API. For a single-node local Cassandra
instance, for example:

```sql
CREATE KEYSPACE url_shortner
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
```

A aplicação cria a tabela `url_shortner` ao iniciar. Os códigos são gerados
por `INCR` atômico no Redis e codificados com Hashids usando alfabeto Base62.
Configure `SHORT_CODE_SECRET_KEY` com no mínimo 6 caracteres (guarde o mesmo
valor em todas as instâncias e não o compartilhe). Hashids garante códigos com
no mínimo quatro caracteres; é uma forma de ofuscação, não criptografia.
O contador Redis é inicializado atomicamente em
`62³ - 1` (ou mantido se já for maior), então o primeiro `INCR` usa `62³`.
O Cassandra usa
`IF NOT EXISTS` como proteção adicional contra colisões com códigos já
persistidos. Todas as instâncias da API devem apontar para o mesmo Redis; no
Compose, o contador fica persistido no volume `redis_data`. Fora do Docker
Compose, configure `REDIS_URL` (padrão `redis://127.0.0.1:6379/0`) e
`SHORT_CODE_SECRET_KEY`, além das variáveis Cassandra:

| Variable | Default | Description |
| --- | --- | --- |
| `CASSANDRA_CONTACT_POINTS` | `127.0.0.1` | Comma-separated Cassandra hosts |
| `CASSANDRA_PORT` | `9042` | Cassandra native transport port |
| `CASSANDRA_KEYSPACE` | `url_shortner` | Existing keyspace |
| `CASSANDRA_USERNAME` | — | Optional username; set with the password |
| `CASSANDRA_PASSWORD` | — | Optional password; set with the username |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis connection URL |
| `SHORT_CODE_SECRET_KEY` | — | Required Hashids salt; use the same value across API instances |

`GET /api/url-shortner/` uses a full-table scan (`ALLOW FILTERING`) to preserve
the current list-all API. This is suitable for a small dataset; a large
production dataset should use a query-specific listing table and pagination.
