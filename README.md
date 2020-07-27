# droplink
Send DAO membership tokens, built as part of [Easy DAO Onboarding](https://github.com/gturkoglu/dao-onboarding) project.

## Requirements

You need to install Flask and `web3.py`.

## Installation


Please read the `app.py` before starting to use the project, code is very short and it is probably easy to understand for you.

You need to create a file called `secrets.ini` and add the required credentials inside this file. An example `secrets.ini` file looks like this:

```python
[secrets]
private_key = <private key>
contract_address = <contract address>
sender_address = <public key of the same private key>
web3_provider = https://rinkeby.infura.io/v3/<infura_key>
```

You can adapt this file for your use case.

Also you need to create a SQLite3 database to store which addresses already received the membership token. I created a SQLite3 database on a file called `droplink.db` and I have created simple table for storing previous addresses.

```
CREATE TABLE addresses(
  address TEXT NOT NULL
  );
```
