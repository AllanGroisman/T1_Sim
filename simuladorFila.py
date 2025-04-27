import random
import heapq

def uniform(a, b):
    """Gera número Uniform(a, b), consumindo 1 random.random()."""
    return a + (b - a) * random.random()

class Queue:
    def __init__(self, num_servers, capacity, arrival_min, arrival_max, service_min, service_max):
        self.num_servers = num_servers
        self.capacity = capacity
        self.arrival_min = arrival_min
        self.arrival_max = arrival_max
        self.service_min = service_min
        self.service_max = service_max

        self.n_in_system = 0      # número de clientes (fila + em serviço)
        self.servers_busy = 0     # servidores ocupados
        self.lost_customers = 0   # clientes perdidos
        self.time_in_state = [0.0] * (capacity + 1)

    def is_full(self):
        return self.n_in_system >= self.capacity

    def add_customer(self):
        if self.n_in_system < self.capacity:
            self.n_in_system += 1
            return True
        else:
            self.lost_customers += 1
            return False

    def remove_customer(self):
        self.n_in_system -= 1

    def need_service_start(self):
        return self.n_in_system > self.servers_busy

    def start_service(self):
        self.servers_busy += 1

    def end_service(self):
        self.servers_busy -= 1

def simulate(arrivals, queue_params, seed, max_random, network):
    if seed is not None:
        random.seed(seed)

    #cria a lista de filas com os parametros passados
    queue_list = []
    for params in queue_params:
        fila = Queue(params[0], params[1], params[2], params[3], params[4], params[5])
        queue_list.append(fila)

    #parametros para controle
    random_used = 0
    current_time = 0.0
    last_time = 0.0
    total_completed = 0

    events = []

    def advance_time(new_time):
        nonlocal current_time, last_time
        dt = new_time - current_time
        if dt > 0:
            for queue in queue_list:
                n = queue.n_in_system
                if n <= queue.capacity:
                    queue.time_in_state[n] += dt
            current_time = new_time
            last_time = new_time

    def get_destination(queue_id):
        queue_probabilities = network[queue_id]
        destination_ids = [id for id, _ in queue_probabilities]
        probabilities = [prob for _, prob in queue_probabilities]
        return random.choices(destination_ids, weights=probabilities, k=1)[0]

    # Agendar todas as chegadas iniciais
    for arrival in arrivals:
        queue_id = arrival[0] - 1
        arrival_time = arrival[1]
        heapq.heappush(events, (arrival_time, 'A' + str(queue_id)))

    while events:
        ev_time, ev_type = heapq.heappop(events)
        advance_time(ev_time)

        if ev_type[0] == "A":
            queue_id = int(ev_type[1:])
            actual_queue = queue_list[queue_id]

            entered = actual_queue.add_customer()

            # Só agora sorteia o tempo da próxima chegada para essa fila
            if actual_queue.arrival_min != 0.0 or actual_queue.arrival_max != 0.0:
                if random_used + 1 > max_random:
                    break
                random_used += 1
                inter_arrival = uniform(actual_queue.arrival_min, actual_queue.arrival_max)
                next_arrival_time = current_time + inter_arrival
                heapq.heappush(events, (next_arrival_time, 'A' + str(queue_id)))

            # Se entrou e tem servidor livre, já inicia serviço
            if entered and actual_queue.servers_busy < actual_queue.num_servers:
                if random_used + 1 > max_random:
                    break
                random_used += 1
                service_time = uniform(actual_queue.service_min, actual_queue.service_max)
                actual_queue.start_service()
                heapq.heappush(events, (current_time + service_time, 'D' + str(queue_id)))

        elif ev_type[0] == "D":
            queue_id = int(ev_type[1:])
            actual_queue = queue_list[queue_id]

            actual_queue.remove_customer()
            actual_queue.end_service()

            if random_used + 1 > max_random:
                break
            random_used += 1

            destination_id = get_destination(queue_id)
            if destination_id == -1:
                total_completed += 1
            else:
                destination_queue = queue_list[destination_id]
                entered = destination_queue.add_customer()
                if entered and destination_queue.servers_busy < destination_queue.num_servers:
                    if random_used + 1 > max_random:
                        break
                    random_used += 1
                    service_time = uniform(destination_queue.service_min, destination_queue.service_max)
                    destination_queue.start_service()
                    heapq.heappush(events, (current_time + service_time, 'D' + str(destination_id)))

            if actual_queue.need_service_start():
                if random_used + 1 > max_random:
                    break
                random_used += 1
                service_time = uniform(actual_queue.service_min, actual_queue.service_max)
                actual_queue.start_service()
                heapq.heappush(events, (current_time + service_time, 'D' + str(queue_id)))

        else:
            raise ValueError(f"Evento inválido detectado: {ev_type}")

    tempo_final = current_time

    queue_times = [queue.time_in_state for queue in queue_list]
    queue_lost_customers = [queue.lost_customers for queue in queue_list]

    return tempo_final, queue_times, queue_lost_customers, total_completed

def fila_simples():
        chegadas = [(1, 2.0)]
        lista_queues = [
            (1, 5, 1.0, 2.0, 1.5, 3.0)
        ]
        network = [[(-1, 1.0)]]
        return chegadas, lista_queues, network

def fila_tandem():
    chegadas = [(1, 2.0)]
    lista_queues = [
        (1, 5, 1.0, 2.0, 1.5, 3.0),
        (1, 5, None, None, 2.0, 4.0)
    ]
    network = [
        [(1, 1.0)],
        [(-1, 1.0)]
    ]
    return chegadas, lista_queues, network

def multifilas():
    chegadas = [(1, 2.0)]
    lista_queues = [
        (1, 99999, 2.0, 4.0, 1.0, 2.0),
        (2, 5, 0.0, 0.0, 4.0, 8.0),
        (2, 10, 0.0, 0.0, 5.0, 15.0)
    ]
    network = [
        [(1, 0.8), (2, 0.2)],
        [(0, 0.3), (1, 0.5), (-1, 0.2)],
        [(2, 0.7), (-1, 0.3)]
    ]
    return chegadas, lista_queues, network

if __name__ == "__main__":

    # AQUI TU PODE ALTERAR MANUALMENTE AS CONFIGURACOES DA REDE DE FILAS
    #LISTA DE CHEGADAS
    chegadas = [(1, 2.0)]

    #LISTA DE FILAS
    # Segue o formato para cada fila:
    # (numServidores,capacidade,minChegada,maxChegada,minServico,maxServico)
    lista_queues = [
        (1, 99999, 2.0, 4.0, 1.0, 2.0), #q1
        (2, 5, 0.0, 0.0, 4.0, 8.0), #q2
        (2, 10, 0.0, 0.0, 5.0, 15.0) #q3
    ]
    #LISTA DE CONEXOES DAS FILAS
    # Segue o formato para cada fila:
    # [(destino,probabilidade)(destino2,probabilidade2)]
    network = [
        [(1, 0.8), (2, 0.2)], #q1
        [(0, 0.3), (1, 0.5), (-1, 0.2)], #q2
        [(2, 0.7), (-1, 0.3)] #q3
    ]


    # SE NAO QUISER FAZER DE FORMA MANUAL, AQUI TEM ALGUMAS PRONTAS
    config = multifilas() #A DO T1
    #config = fila_simples() 
    #config = fila_tandem()

    #SE FOR USAR AS PRONTAS, BASTA DESCOMENTAR ISSO
    chegadas, lista_queues, network = config

    tfinal, queue_times, queue_lost_customers, completed = simulate(
        arrivals=chegadas,
        queue_params=lista_queues,
        seed=42,
        max_random=100_000,
        network=network
    )

    print("="*50)
    print("============== REPORT ==============")
    print("="*50)

    for i in range(len(lista_queues)):
        servidores, capacidade, chegada_min, chegada_max, servico_min, servico_max = lista_queues[i]
        tempos = queue_times[i]
        perdidos = queue_lost_customers[i]

        print("-" * 50)
        print(f"Fila Q{i+1}: {servidores} servidores, capacidade {capacidade}")

        if chegada_min != 0.0 or chegada_max != 0.0:
            print(f"Chegada entre {chegada_min} e {chegada_max}")
        
        print(f"Serviço entre {servico_min} e {servico_max}")
        print("-" * 50)

        tempo_total = sum(tempos)
        if tempo_total > 0:
            print("Estado  Tempo  Probabilidade")
            for estado in range(len(tempos)):
                if tempos[estado] > 0:
                    prob = tempos[estado] / tempo_total
                    print(f"{estado:6d} {tempos[estado]:8.2f} {prob:14.2%}")
        
        print(f"Clientes perdidos: {perdidos}\n")

    print("-" * 50)
    print(f"Tempo da simulação: {tfinal:.2f}")
    print("-" * 50)

