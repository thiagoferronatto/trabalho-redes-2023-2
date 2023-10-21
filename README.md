# [ Título do jogo aqui ]

## Como rodar?

### Instruções

1. Tenha o Python instalado, preferencialmente a versão 3.12;
2. Instale a biblioteca Argon2 (`python -m pip install argon2-cffi`);
3. Execute os módulos relevantes (`python [nome-do-módulo].py`);

### Exemplo

```
trabalho-redes-2023-2$ python -m pip install argon2-cffi
trabalho-redes-2023-2$ python ias.py &
trabalho-redes-2023-2$ python player.py meu_username minha_senha
```

## Arquivos

### `ias.py`

Representa o servidor de informação e autenticação. Qualquer pessoa que deseja participar de partidas necessitará de um registro no IAS, assim como um _token_ de autenticação ativo obtido via _login_ pelo mesmo servidor. Ele, no entanto, não é utilizado só por clientes; o servidor de _matchmaking_ também faz uso de suas funcionalidades para validação de _tokens_ de jogadores.

### `ias_interface_data.py`

Contém dados de fronteira sobre o IAS. Deve ser importado em módulos que utilizam autenticação, tendo em vista que possui os dados necessários para efetivação da conexão.

### `mms.py`

Representa o servidor de _matchmaking_. Jogadores cadastrados no IAS podem solicitar uma entrada na fila de _matchmaking_ para que, assim que houver paridade, uma partida seja proposta entre dois deles. Jogadores podem aceitar ou recusar uma partida; ao aceitar, ambos os _players_ são removidos da fila e iniciam uma conexão direta para dar início à partida; ao recusar, somente o jogador que recusou (a não ser que ambos tenham recusado) será removido da fila, enquanto o outro continua à procura de uma partida. Jogadores podem, também, solicitar remoção da fila.

### `mms_interface_data.py`

Contém dados de fronteira sobre o MMS. Deve ser importado em módulos que desejam conectar-se ao sistema de _matchmaking_.

### `player.py`

Representa um cliente. Após criar uma conta e autenticar-se no IAS, um cliente pode solicitar entrada na fila de _matchmaking_ do MMS, efetivamente tornando-se um jogador. Aqui são implementadas tanto a lógica das conexões com o IAS e o MMS quanto a lógica do jogo em si.

### `style.py`

Contém funções que encapsulam -- e consequentemente facilitam -- o uso de textos coloridos em janelas de terminal. São extensivamente utilizadas para _logging_ de informações em ambos os lados das conexões.

## Justificativa para as bibliotecas

- **Argon2**: Armazenamento de senhas.
