# droplink
Send DAO membership tokens, built as part of [Easy DAO Onboarding](https://github.com/gturkoglu/dao-onboarding) project.

## Features

* User & session management
* Sending DAO membership tokens

## Demo

Example instance of `droplink` is hosted on the [droplink.gokdeniz.me](https://droplink.gokdeniz.me). This instance provides MOK, membership token for [token.aragonid.eth](https://rinkeby.aragon.org/#/token.aragonid.eth), DAO hosted on Rinkeby test network.

## Requirements

You need to install Flask and `web3.py`. Also I use needle.sh for application security but it is not required.

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

Also you need to create a SQLite3 database to store users and see which users already received the membership token. I created a SQLite3 database on a file called `droplink.db` and I have created two tables for storing sessions and users.

```
CREATE TABLE users(
  username TEXT NOT NULL, 
  password TEXT NOT NULL, 
  address TEXT NOT NULL, 
  received TEXT
 );

CREATE TABLE sessions(
  username TEXT NOT NULL, 
  session TEXT NOT NULL
 );
```
