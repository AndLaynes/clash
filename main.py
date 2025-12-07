import os
import json
import requests
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

# Configurações
CLAN_TAG = "%239PJRJRPC"  # Tag fixa do clã (#9PJRJRPC)
API_BASE_URL = "https://api.clashroyale.com/v1"
API_KEY = os.environ.get("CR_API_KEY")
DATA_DIR = "data"

def get_headers():
    if not API_KEY:
        return None
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

def save_json(data, filename):
    """Salva dados em arquivo JSON no diretório data."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Dados salvos em: {filepath}")

def load_json(filename):
    """Carrega dados de arquivo JSON do diretório data."""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            print(f"Carregando cache local: {filepath}")
            return json.load(f)
    return None

def fetch_data(endpoint):
    """Busca dados da API."""
    headers = get_headers()
    if not headers:
        return None
    
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar API ({url}): {e}")
        return None

def get_data_with_cache(endpoint, filename):
    """
    Tenta buscar da API e salvar.
    Se falhar (sem chave, sem net, erro), tenta carregar do cache.
    """
    data = fetch_data(endpoint)
    if data:
        save_json(data, filename)
        return data
    
    print(f"Tentando usar cache local para {filename}...")
    cached_data = load_json(filename)
    if cached_data:
        return cached_data
    
    print(f"AVISO: Não foi possível obter dados para {filename} (nem API, nem Cache).")
    return None

def calculate_league(war_trophies):
    """
    Calcula a liga atual baseado nos troféus de guerra.
    Retorna: (nome_liga, próximo_threshold, troféus_faltantes, progresso_percentual, próxima_liga)
    """
    # Ligas do Clash Royale (baseado em pesquisa)
    leagues = [
        ("Bronze I", 0, 200),
        ("Bronze II", 200, 400),
        ("Bronze III", 400, 600),
        ("Silver I", 600, 900),
        ("Silver II", 900, 1200),
        ("Silver III", 1200, 1500),
        ("Gold I", 1500, 2000),
        ("Gold II", 2000, 2500),
        ("Gold III", 2500, 3000),
        ("Legendary", 3000, 5000)
    ]
    
    current_league = "Bronze I"
    next_league = "Bronze II"
    next_threshold = 200
    current_min = 0
    
    for i, (league_name, min_trophies, max_trophies) in enumerate(leagues):
        if war_trophies >= min_trophies and war_trophies < max_trophies:
            current_league = league_name
            next_threshold = max_trophies
            current_min = min_trophies
            # Próxima liga
            if i + 1 < len(leagues):
                next_league = leagues[i + 1][0]
            else:
                next_league = "Legendary"
            break
        elif war_trophies >= max_trophies:
            current_league = league_name
            next_threshold = max_trophies
            current_min = min_trophies
            if i + 1 < len(leagues):
                next_league = leagues[i + 1][0]
            else:
                next_league = "Legendary"
    
    trophies_to_next = max(0, next_threshold - war_trophies)
    
    # Calcular progresso percentual dentro da liga atual
    league_range = next_threshold - current_min
    if league_range > 0:
        progress_in_league = war_trophies - current_min
        progress_pct = min(100, (progress_in_league / league_range) * 100)
    else:
        progress_pct = 100
    
    return current_league, next_threshold, trophies_to_next, int(progress_pct), next_league

def get_war_day_target():
    """Calcula a meta de decks para o dia atual (baseado em Brasília/UTC-3)."""
    # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom
    today = datetime.now().weekday()
    
    # War Days: Qui (3) -> 1, Sex (4) -> 2, Sab (5) -> 3, Dom (6) -> 4
    # Se for outro dia, assume meta máxima ou 0? Vamos assumir que estamos vendo "resultados de ontem" se for seg ou ter.
    # Mas o screenshot diz "Sábado: Audita Sexta (Meta: 8)".
    # Se hoje é Sábado, estamos no dia 3 de guerra, mas auditamos o dia 2.
    # Vamos simplificar: Retornar o alvo acumulado que DEVERIA ter sido atingido até HOJE no final do dia.
    
    # Ajuste: A guerra começa quinta.
    # Quinta (Dia 1): Meta 4
    # Sexta (Dia 2): Meta 8
    # Sábado (Dia 3): Meta 12
    # Domingo (Dia 4): Meta 16
    
    targets = {
        3: 4,   # Quinta
        4: 8,   # Sexta
        5: 12,  # Sábado
        6: 16   # Domingo
    }
    
    # Se for segunda, terça ou quarta, mostra resultado final (16) ou 0?
    if today in targets:
        return targets[today], today
    else:
        return 16, today # Fora dos dias de guerra, assume meta total


def main():
    print("=== JULES Squad: Clash Royale Dashboard Generator ===")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # 1. Obter dados (API -> Cache -> Memória)
    # Normaliza tag para uso na API se necessário (embora a URL use %23)
    # A URL precisa de %23. O endpoint é /clans/%23TAG
    
    clan_info = get_data_with_cache(f"/clans/{CLAN_TAG}", "clan_info.json")
    current_war = get_data_with_cache(f"/clans/{CLAN_TAG}/currentriverrace", "current_war.json")
    war_log = get_data_with_cache(f"/clans/{CLAN_TAG}/riverracelog?limit=20", "war_log.json")
    
    if not clan_info:
        print("ERRO CRÍTICO: Não há dados do clã para gerar o dashboard.")
        return

    # Dados processados para o template
    context = {
        "clan": clan_info,
        "war": current_war,
        "war_log": war_log,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    # 2. Configurar Jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    template_index = env.get_template("index.html")
    template_history = env.get_template("war_history.html")
    template_members = env.get_template("members_stats.html")
    template_members = env.get_template("members_stats.html")
    template_ranking = env.get_template("ranking.html")
    template_audit = env.get_template("audit.html")

    # 3. Renderizar HTML Index

    # 3. Renderizar HTML Index
    html_content_index = template_index.render(context)
    
    # 3.2 Processar Auditoria
    audit_target_decks, weekday_idx = get_war_day_target()
    days_map = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    current_day_name = days_map[weekday_idx]
    
    # Mapear dias de guerra para exibição (1 a 4)
    war_day_num = weekday_idx - 2 if 3 <= weekday_idx <= 6 else 4
    if war_day_num < 1: war_day_num = 4 # Fallback
    
    audit_context = {
        "clan": clan_info, 
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "audit_day": current_day_name,
        "war_day": war_day_num,
        "target_decks": audit_target_decks,
        "target_decks_total": 16
    }
    
    audit_results = []
    stats_counts = {"on_track": 0, "incomplete": 0, "zero": 0}
    
    if clan_info and "memberList" in clan_info:
        # Criar mapa de decks usados na guerra atual
        war_participants_map = {}
        if current_war and "clan" in current_war and "participants" in current_war["clan"]:
            for p in current_war["clan"]["participants"]:
                war_participants_map[p["tag"]] = p.get("decksUsed", 0)
        
        # Iterar sobre MEMBROS ATUAIS (para garantir que quem saiu não apareça, e quem entrou apareça zerado)
        for member in clan_info["memberList"]:
            tag = member["tag"]
            decks_used = war_participants_map.get(tag, 0)
            
            missing = max(0, audit_target_decks - decks_used)
            
            status_label = "Em Dia"
            status_class = "success"
            
            if decks_used == 0:
                status_label = "Zerado"
                status_class = "danger"
                stats_counts["zero"] += 1
            elif missing > 0:
                status_label = "Incompleto"
                status_class = "warning"
                stats_counts["incomplete"] += 1
            else:
                stats_counts["on_track"] += 1
                
            audit_results.append({
                "name": member["name"],
                "tag": tag,
                "role": member["role"],
                "decks_used": decks_used,
                "missing": missing,
                "status_label": status_label,
                "status_class": status_class
            })
            
        # Ordenar: Zerados primeiro, depois incompletos, depois em dia
        audit_results.sort(key=lambda x: (x["missing"], -x["decks_used"]), reverse=True)
        
        audit_context.update({
            "audit_results": audit_results,
            "stats": stats_counts
        })
        
    html_content_audit = template_audit.render(audit_context)
    
    # 3.5 Processar dados de Membros
    members_context = {"clan": clan_info}
    if clan_info and "memberList" in clan_info:
        members = clan_info["memberList"]
        
        # Calcular estatísticas
        total_donations = sum(m.get("donations", 0) for m in members)
        avg_trophies = int(sum(m.get("trophies", 0) for m in members) / len(members)) if members else 0
        
        # Calcular dias offline (mockado, API não fornece isso diretamente em memberList)
        # Pode ser calculado se tivermos battleLog ou outro endpoint
        for member in members:
            # Placeholder - em produção, seria calculado via lastSeenTime ou battleLog
            member["lastSeen"] = 0  # 0 = online hoje
        
        members_context.update({
            "members": members,
            "total_donations": total_donations,
            "avg_trophies": avg_trophies
        })
    
    html_content_members = template_members.render(members_context)
    
    # 5.5 Processar Ranking
    ranking_context = {"clan": clan_info, "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M")}
    if clan_info and "memberList" in clan_info:
        members = clan_info["memberList"]
        sorted_by_trophies = sorted(members, key=lambda x: x.get("trophies", 0), reverse=True)
        
        for member in members:
            member["war_score"] = member.get("donations", 0) * 10 + member.get("trophies", 0) // 100
        
        # Preparar dados para o gráfico (top 10)
        top_10 = sorted_by_trophies[:10]
        ranking_chart_data = {
            "labels": [p["name"][:10] + "..." if len(p["name"]) > 10 else p["name"] for p in top_10],
            "trophies": [p.get("trophies", 0) for p in top_10]
        }
        
        ranking_context.update({
            "top_players": sorted_by_trophies[:3],
            "all_players": sorted_by_trophies,
            "ranking_chart_data": ranking_chart_data
        })
    
    html_content_ranking = template_ranking.render(ranking_context)

    # 4. Processar Histórico de Guerra (Última Guerra)
    history_context = {"clan": clan_info, "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M")}
    
    # Calcular Liga baseada em troféus de guerra
    war_trophies = clan_info.get("clanWarTrophies", 0) if clan_info else 0
    league_name, next_threshold, trophies_to_next, progress_pct, next_league_name = calculate_league(war_trophies)
    
    # Processar dados históricos para o gráfico
    war_chart_data = {"labels": [], "fame": []}
    if war_log and "items" in war_log:
        # Limitar às últimas 10 guerras para o gráfico
        recent_wars = war_log["items"][:10]
        recent_wars.reverse()  # Ordem cronológica
        
        target_tag = CLAN_TAG.replace("%23", "#")
        for idx, war in enumerate(recent_wars):
            my_clan_data = next((s for s in war.get("standings", []) if s.get("clan", {}).get("tag") == target_tag), None)
            if my_clan_data:
                war_chart_data["labels"].append(f"S{war.get('sectionIndex', idx+1)}")
                war_chart_data["fame"].append(my_clan_data["clan"].get("fame", 0))
    
    history_context.update({
        "league_name": league_name,
        "next_league_name": next_league_name,
        "next_league_threshold": next_threshold,
        "trophies_to_next": trophies_to_next,
        "league_progress": progress_pct,
        "war_chart_data": war_chart_data
    })
    
    # Processar última guerra
    last_war = None
    if war_log and "items" in war_log and len(war_log["items"]) > 0:
        last_war = war_log["items"][0]
    
    if last_war:
        participants = []
        
        # Encontrar o clã na lista de standings
        # A API retorna a tag com #, mas nossa constante pode estar com %23
        target_tag = CLAN_TAG.replace("%23", "#")
        
        my_clan_standing = next((s for s in last_war["standings"] if s["clan"]["tag"] == target_tag), None)
        
        if my_clan_standing:
            if "participants" in my_clan_standing["clan"]:
                war_participants = my_clan_standing["clan"]["participants"]
                
                # CORREÇÃO CRÍTICA: Filtrar apenas jogadores ATIVOS do clã
                # Criar set de tags de membros ativos
                active_member_tags = set()
                if clan_info and "memberList" in clan_info:
                    active_member_tags = {member["tag"] for member in clan_info["memberList"]}
                
                # Filtrar participantes da guerra que são membros ativos
                clan_participants = [p for p in war_participants if p["tag"] in active_member_tags]
                
                print(f"Total de participantes na guerra: {len(war_participants)}")
                print(f"Participantes ativos (membros atuais): {len(clan_participants)}")
            else:
                clan_participants = []
            
            for p in clan_participants:
                decks_used = p["decksUsed"]
                
                # Lógica de Classificação
                status_label = "Perigo"
                status_class = "danger"
                
                if decks_used == 16:
                    status_label = "Campeão"
                    status_class = "champion"
                elif 12 <= decks_used <= 15:
                    status_label = "Atenção"
                    status_class = "warning"
                
                participants.append({
                    "name": p["name"],
                    "tag": p["tag"],
                    "decksUsed": decks_used,
                    "fame": p["fame"],
                    "status_label": status_label,
                    "status_class": status_class
                })
            
            # Ordenar por decks usados (desc) e depois fama (desc)
            participants.sort(key=lambda x: (x["decksUsed"], x["fame"]), reverse=True)
            
            history_context.update({
                "season_id": last_war["seasonId"],
                "section_index": last_war["sectionIndex"],
                "participants": participants
            })
    else:
        print("Aviso: Nenhum histórico de guerra encontrado para gerar a tabela detalhada.")

    # 5. Renderizar HTML Histórico
    html_content_history = template_history.render(history_context)

    # 6. Salvar arquivos
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content_index)
    
    with open("war_history.html", "w", encoding="utf-8") as f:
        f.write(html_content_history)
    
    with open("members_stats.html", "w", encoding="utf-8") as f:
        f.write(html_content_members)
    
    with open("ranking.html", "w", encoding="utf-8") as f:
        f.write(html_content_ranking)

    with open("audit.html", "w", encoding="utf-8") as f:
        f.write(html_content_audit)
    
    print(f"\n=== SUCESSO ===")
    print(f"Arquivos gerados:")
    print(f"1. {os.path.abspath('index.html')}")
    print(f"2. {os.path.abspath('war_history.html')}")
    print(f"3. {os.path.abspath('members_stats.html')}")
    print(f"4. {os.path.abspath('ranking.html')}")
    print(f"5. {os.path.abspath('audit.html')}")
    print(f"Dados brutos salvos em: {os.path.abspath(DATA_DIR)}")

if __name__ == "__main__":
    main()
