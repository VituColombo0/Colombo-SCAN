"""
Colombo Scanner v4.0 — Main Entry Point
Modos clássicos com opção inteligente de multi-alvos.
"""
import argparse
import sys
from ui.prompts import menu_principal, perguntar_alvos, escolher_plugins_manual, menu_exportacao, perguntar_parametros_auto
from ui.components import print_banner, exibir_tutorial, console
from core.engine import ColomboEngine
from core.ui import exibir_resultados
from core.report import gerar_relatorio
from core.graph import gerar_grafo
from core.cases import selecionar_ou_criar_case, menu_gerenciar_cases
from core.health_check import check_dependencies

def main():
    parser = argparse.ArgumentParser(description="Colombo Scanner v4.0")
    parser.add_argument("--alvo", help="Alvo para varredura silenciosa")
    args = parser.parse_args()

    engine = ColomboEngine()

    if args.alvo:
        # Modo Silencioso
        resultados = engine.run_direct_scan(args.alvo)
        exibir_resultados(resultados)
        gerar_relatorio(args.alvo, resultados)
        sys.exit(0)

    # Modo Interativo
    check_dependencies()
    case_id = selecionar_ou_criar_case()

    while True:
        print_banner(len(engine.plugins))
        escolha = menu_principal()

        if escolha == "sair" or escolha is None: break
        if escolha == "tutorial": exibir_tutorial(); continue
        if escolha == "cases": menu_gerenciar_cases(); continue

        if escolha in ["auto", "manual"]:
            alvos = []
            resultados = []

            if escolha == "auto":
                alvos = perguntar_alvos("Alvo(s) (para vários, separe por vírgula):")
                if not alvos: continue
                
                params = perguntar_parametros_auto()
                
                resultados = engine.run_multi_target_scan(
                    alvos, 
                    case_id=case_id, 
                    aprofundar=params["aprofundar"],
                    layers=params["layers"]
                )

            elif escolha == "manual":
                # Agrupa plugins por categoria
                cats = {}
                for p in engine.plugins:
                    cat = p.get("category", "Outros")
                    cats.setdefault(cat, []).append(p)
                
                plugins_selecionados = escolher_plugins_manual(cats)
                if not plugins_selecionados: continue
                
                alvos = perguntar_alvos("Alvo(s) para ferramentas selecionadas:")
                if not alvos: continue
                
                if len(alvos) > 1:
                    # Roda manual para cada alvo (a funcao atual run_manual_scan so aceita 1 target dicio)
                    for a in alvos:
                        res = engine.run_manual_scan(plugins_selecionados, {"alvo": a}, case_id=case_id)
                        resultados.extend(res)
                else:
                    resultados = engine.run_manual_scan(plugins_selecionados, {"alvo": alvos[0]}, case_id=case_id)
            
            if resultados:
                exibir_resultados(resultados)
                
                alvo_nome = alvos[0] if len(alvos) == 1 else f"Multi-{len(alvos)}-alvos"
                
                # Exportações
                exports = menu_exportacao(alvo_nome)
                if exports:
                    if any(x in exports for x in ["pdf", "json", "csv"]):
                        path = gerar_relatorio(alvo_nome, resultados)
                        console.print(f"[green]✅ Relatório salvo em {path}[/green]")
                    if "grafo" in exports:
                        path = gerar_grafo(alvo_nome, resultados)
                        console.print(f"[green]✅ Grafo salvo em {path}[/green]")
                
                input("\nPressione ENTER para continuar...")

if __name__ == "__main__":
    main()
