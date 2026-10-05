import hashlib
import datetime


class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Блок {self.index} замайнен: nonce={self.nonce}, hash={self.hash[:20]}...")


class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.difficulty = difficulty
        # Фиксированная временная метка для генезис-блока,
        # чтобы у всех узлов получился одинаковый генезис-блок
        genesis_block = Block(0, "2025-01-01 00:00:00", "Genesis Block", "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    def add_block(self, data):
        index = len(self.chain)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        previous_hash = self.chain[-1].hash
        new_block = Block(index, timestamp, data, previous_hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def add_block_without_validation(self, block):
        self.chain.append(block)

    def is_valid(self):
        if len(self.chain) == 0:
            return False
        genesis = self.chain[0]
        if genesis.index != 0 or genesis.previous_hash != "0":
            return False
        if not genesis.hash.startswith('0' * self.difficulty):
            return False
        if genesis.hash != genesis.calculate_hash():
            return False
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.index != previous.index + 1:
                return False
            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.calculate_hash():
                return False
            if not current.hash.startswith('0' * self.difficulty):
                return False
        return True

    def is_block_valid(self, block):
        if block.index != len(self.chain):
            return False
        if block.previous_hash != self.chain[-1].hash:
            return False
        if block.hash != block.calculate_hash():
            return False
        if not block.hash.startswith('0' * self.difficulty):
            return False
        return True


class Node:
    def __init__(self, node_id, difficulty=4):
        self.node_id = node_id
        self.blockchain = Blockchain(difficulty)
        self.peers = []

    def add_peer(self, peer_node):
        self.peers.append(peer_node)

    def broadcast_block(self, block):
        for peer in self.peers:
            peer.receive_block(block)

    def create_and_broadcast_block(self, data):
        print(f"\n{self.node_id}: Начинаю майнинг блока с данными '{data}'")
        index = len(self.blockchain.chain)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        previous_hash = self.blockchain.chain[-1].hash
        new_block = Block(index, timestamp, data, previous_hash)
        new_block.mine_block(self.blockchain.difficulty)
        print(f"{self.node_id}: Блок замайнен, рассылаю...")
        self.broadcast_block(new_block)
        return new_block

    def receive_block(self, block):
        if block.index != len(self.blockchain.chain):
            print(
                f"{self.node_id}: Отклонён блок {block.index} - неверный индекс (ожидался {len(self.blockchain.chain)})")
            return False

        if self.blockchain.is_block_valid(block):
            if not self.has_block_at_index(block.index):
                self.blockchain.add_block_without_validation(block)
                self.broadcast_block(block)
                print(f"{self.node_id}: Принял блок {block.index} с данными '{block.data}'")
                return True
            else:
                print(f"{self.node_id}: Отклонён блок {block.index} - уже существует")
                return False
        else:
            print(f"{self.node_id}: Отклонён блок {block.index} - недействительный хэш или nonce")
            return False

    def has_block_at_index(self, index):
        return index < len(self.blockchain.chain)


# ============================================================
# Шаг 5: Симуляция одновременного майнинга и проверка консенсуса
# ============================================================

print("=== Создание узлов ===")
node1 = Node("Node_1", difficulty=4)
node2 = Node("Node_2", difficulty=4)
node3 = Node("Node_3", difficulty=4)

# Проверяем, что у всех узлов одинаковый генезис-блок
print(f"Хэш генезис-блока Node_1: {node1.blockchain.chain[0].hash[:20]}...")
print(f"Хэш генезис-блока Node_2: {node2.blockchain.chain[0].hash[:20]}...")
print(f"Хэш генезис-блока Node_3: {node3.blockchain.chain[0].hash[:20]}...")

# Соединение узлов в сеть
node1.add_peer(node2)
node1.add_peer(node3)
node2.add_peer(node1)
node2.add_peer(node3)
node3.add_peer(node1)
node3.add_peer(node2)

print("\n=== Симуляция: Node1 и Node2 одновременно майнят блок 1 ===")

# Оба узла параллельно готовят блок с index=1
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

block1 = Block(1, timestamp, "Транзакция А", node1.blockchain.chain[-1].hash)
block2 = Block(1, timestamp, "Транзакция В", node2.blockchain.chain[-1].hash)

print(f"\nNode_1: майню блок 1 с данными 'Транзакция А'")
block1.mine_block(node1.blockchain.difficulty)

print(f"\nNode_2: майню блок 1 с данными 'Транзакция В'")
block2.mine_block(node2.blockchain.difficulty)

print("\n=== Рассылка блоков ===")
print("\nNode_1 рассылает свой блок первым:")
node1.broadcast_block(block1)

print("\nNode_2 рассылает свой блок (опоздал):")
node2.broadcast_block(block2)

print("\n=== Проверка состояния цепочек ===")
print(f"Node1 последний блок: {node1.blockchain.chain[-1].data}")
print(f"Node2 последний блок: {node2.blockchain.chain[-1].data}")
print(f"Node3 последний блок: {node3.blockchain.chain[-1].data}")

print(f"\nДлина цепочек:")
print(f"Node1: {len(node1.blockchain.chain)}")
print(f"Node2: {len(node2.blockchain.chain)}")
print(f"Node3: {len(node3.blockchain.chain)}")

print(f"\nПроверка целостности цепочек:")
print(f"Node1: {node1.blockchain.is_valid()}")
print(f"Node2: {node2.blockchain.is_valid()}")
print(f"Node3: {node3.blockchain.is_valid()}")

# ============================================================
# Шаг 6: Проверка защиты от подделки
# ============================================================

print("\n\n=== Проверка защиты от подделки ===")

test_node = Node("Test_Node", difficulty=4)
test_node.blockchain.add_block("Блок 1")
test_node.blockchain.add_block("Блок 2")
test_node.blockchain.add_block("Блок 3")

print(f"\nИсходная цепочка валидна: {test_node.blockchain.is_valid()}")

# Искусственно изменяем данные во втором блоке
print("\n--- Изменяем данные в блоке 1 ---")
test_node.blockchain.chain[1].data = "Изменённые данные"
print(f"Цепочка после изменения данных валидна: {test_node.blockchain.is_valid()}")

# Пытаемся пересчитать хэш без майнинга (со старым nonce)
print("\n--- Пересчитываем хэш без майнинга (nonce остаётся старым) ---")
test_node.blockchain.chain[1].hash = test_node.blockchain.chain[1].calculate_hash()
print(f"Хэш блока 1: {test_node.blockchain.chain[1].hash[:20]}...")
print(f"Цепочка валидна: {test_node.blockchain.is_valid()}")
print(f"Хэш не начинается с {'0' * test_node.blockchain.difficulty} — проверка PoW не пройдена")

# Пытаемся перемайнить блок
print("\n--- Перемайниваем блок 1 (оцениваем вычислительные затраты) ---")
test_node.blockchain.chain[1].nonce = 0
test_node.blockchain.chain[1].hash = test_node.blockchain.chain[1].calculate_hash()
test_node.blockchain.chain[1].mine_block(test_node.blockchain.difficulty)
print(f"Цепочка после перемайнинга блока 1 валидна: {test_node.blockchain.is_valid()}")
print("Примечание: изменение одного блока нарушает связи со всеми последующими блоками")