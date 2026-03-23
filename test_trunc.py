from main import formatar_saida_terminal

teste = "<html><head><title>Teste</title></head><body>" + "oi " * 2000 + "</body></html>"
print("Saída original leng:", len(teste))
print("===")
print(formatar_saida_terminal(teste))
