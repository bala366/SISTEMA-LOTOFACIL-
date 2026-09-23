import re
import math
import random
from collections import Counter
from itertools import combinations, islice

UNIVERSO = tuple(range(1, 26))
MOLDURA = {1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25}
TOTAL_CANDIDATOS = 250000
TOTAL_UNIVERSO = 3268760

_estado = {}

def media(lista): return sum(lista) / len(lista) if lista else 0

def desvio(lista):
    if len(lista) < 2: return 0
    m = media(lista)
    return math.sqrt(sum((x-m)**2 for x in lista) / len(lista))

def ler_resultados_texto(conteudo):
    concursos = {}
    for linha in conteudo.splitlines():
        nums = [int(x) for x in re.findall(r"\d+", linha)]
        if len(nums) < 16: continue
        concurso, dezenas = nums[0], nums[1:16]
        if concurso >= 1 and len(dezenas)==15 and len(set(dezenas))==15 and all(1<=n<=25 for n in dezenas):
            concursos[concurso] = tuple(sorted(dezenas))
    return concursos

def caracteristicas(jogo, anterior=None):
    s=set(jogo); pares=sum(1 for n in jogo if n%2==0); moldura=len(s&MOLDURA)
    repetidas=len(s&set(anterior)) if anterior is not None else 0
    linhas=[]
    for linha in range(5):
        inicio=linha*5+1; linhas.append(len(s&set(range(inicio,inicio+5))))
    colunas=[]
    for coluna in range(5):
        grupo={coluna+1,coluna+6,coluna+11,coluna+16,coluna+21}; colunas.append(len(s&grupo))
    maior_seq=1; atual=1; ordenado=sorted(jogo)
    for i in range(1,len(ordenado)):
        if ordenado[i]==ordenado[i-1]+1:
            atual+=1; maior_seq=max(maior_seq,atual)
        else: atual=1
    return {"soma":sum(jogo),"pares":pares,"impares":15-pares,"moldura":moldura,"miolo":15-moldura,
            "repetidas":repetidas,"linhas":tuple(linhas),"colunas":tuple(colunas),"sequencia":maior_seq}

def analisar_historico(resultados):
    somas=[]; pares=[]; molduras=[]; repetidas=[]; sequencias=[]; pl=Counter(); pc=Counter(); anterior=None
    for jogo in resultados:
        c=caracteristicas(jogo,anterior); somas.append(c["soma"]); pares.append(c["pares"]); molduras.append(c["moldura"]); sequencias.append(c["sequencia"])
        pl[c["linhas"]]+=1; pc[c["colunas"]]+=1
        if anterior is not None: repetidas.append(c["repetidas"])
        anterior=jogo
    return {"soma_media":media(somas),"soma_dp":desvio(somas),"pares_freq":Counter(pares),"moldura_freq":Counter(molduras),
            "repetidas_freq":Counter(repetidas),"sequencia_freq":Counter(sequencias),"linhas_freq":pl,"colunas_freq":pc}

def frequencias(resultados,janela=None):
    dados=resultados[-min(janela,len(resultados)):] if janela is not None else resultados; c=Counter()
    for jogo in dados: c.update(jogo)
    return {n:c[n] for n in UNIVERSO}

def calcular_atrasos(resultados):
    atraso={}; total=len(resultados)
    for n in UNIVERSO:
        achou=None
        for i in range(total-1,-1,-1):
            if n in resultados[i]: achou=total-1-i; break
        atraso[n]=total if achou is None else achou
    return atraso

def calcular_rotacao(resultados,janela=30):
    dados=resultados[-min(janela,len(resultados)):]; rotacao={}
    for n in UNIVERSO:
        estados=[1 if n in jogo else 0 for jogo in dados]
        rotacao[n]=sum(1 for i in range(1,len(estados)) if estados[i]!=estados[i-1])
    return rotacao

def normalizar(dic):
    valores=list(dic.values()); minimo=min(valores); maximo=max(valores)
    if maximo==minimo: return {k:.5 for k in dic}
    return {k:(dic[k]-minimo)/(maximo-minimo) for k in dic}

def criar_score_dezenas(resultados):
    ft=frequencias(resultados); f10=frequencias(resultados,10); f20=frequencias(resultados,20); f50=frequencias(resultados,50); f100=frequencias(resultados,100)
    atrasos=calcular_atrasos(resultados); rotacao=calcular_rotacao(resultados,30)
    nt=normalizar(ft); n10=normalizar(f10); n20=normalizar(f20); n50=normalizar(f50); n100=normalizar(f100); nr=normalizar(rotacao); score={}
    for n in UNIVERSO:
        sa=math.exp(-((atrasos[n]-2.0)**2)/18.0)
        score[n]=.15*nt[n]+.15*n100[n]+.18*n50[n]+.18*n20[n]+.12*n10[n]+.12*nr[n]+.10*sa
    return score

def freq_score(contador,valor):
    if not contador: return 0
    maior=max(contador.values()); return 0 if maior==0 else contador.get(valor,0)/maior

def score_jogo(jogo,ultimo,sd,h):
    c=caracteristicas(jogo,ultimo); s_dezenas=sum(sd[n] for n in jogo)/15
    s_soma=1 if h["soma_dp"]<=0 else math.exp(-(abs(c["soma"]-h["soma_media"])/h["soma_dp"])**2/2)
    sf=.40*s_dezenas+.10*freq_score(h["repetidas_freq"],c["repetidas"])+.09*s_soma+.08*freq_score(h["pares_freq"],c["pares"])+.08*freq_score(h["moldura_freq"],c["moldura"])+.07*freq_score(h["linhas_freq"],c["linhas"])+.07*freq_score(h["colunas_freq"],c["colunas"])+.06*freq_score(h["sequencia_freq"],c["sequencia"])
    if c["repetidas"]<7: sf*=.70
    if c["repetidas"]>11: sf*=.65
    if c["pares"]<5: sf*=.70
    if c["pares"]>10: sf*=.70
    if c["moldura"]<7: sf*=.75
    if c["moldura"]>13: sf*=.75
    return sf,c

def gerar_jogo_ponderado(sd):
    disponiveis=list(UNIVERSO); jogo=[]
    for _ in range(15):
        pesos=[max(sd[n],.01)**2.2 for n in disponiveis]
        escolhido=random.choices(disponiveis,weights=pesos,k=1)[0]; jogo.append(escolhido); disponiveis.remove(escolhido)
    return tuple(sorted(jogo))

def melhor(a,b):
    if b is None: return True
    if a[0]>b[0]: return True
    if a[0]==b[0] and a[1]<b[1]: return True
    return False

def fmt_jogo(j): return " ".join("%02d" % n for n in j)

def bloco(titulo,r):
    sc,j,c=r; linhas_txt="-".join(map(str,c["linhas"])); colunas_txt="-".join(map(str,c["colunas"]))
    return (titulo+"\n"+fmt_jogo(j)+"\n\nScore: %.8f"%sc+"\nRepetidas: %d"%c["repetidas"]+
            "\nPares/Ímpares: %d/%d"%(c["pares"],c["impares"])+"\nSoma: %d"%c["soma"]+
            "\nMoldura/Miolo: %d/%d"%(c["moldura"],c["miolo"])+"\nLinhas: "+linhas_txt+
            "\nColunas: "+colunas_txt+"\nMaior sequência: %d"%c["sequencia"])

def iniciar(conteudo):
    global _estado
    concursos=ler_resultados_texto(conteudo)
    if len(concursos)<20:
        _estado={}; return "ERRO|Histórico insuficiente ou arquivo não reconhecido."
    numeros=sorted(concursos); resultados=[concursos[n] for n in numeros]; ultimo=resultados[-1]
    hist=analisar_historico(resultados); sd=criar_score_dezenas(resultados)
    ranking=sorted(UNIVERSO,key=lambda n:(-sd[n],n)); base=tuple(sorted(ranking[:15])); sc,car=score_jogo(base,ultimo,sd,hist)
    _estado={"numeros":numeros,"ultimo":ultimo,"hist":hist,"sd":sd,"campeao_250":(sc,base,car),"vistos":{base},
             "feito_250":0,"iter_universo":None,"feito_universo":0,"campeao_universo":None}
    return "OK|Concursos %d a %d carregados."%(numeros[0],numeros[-1])

def passo_250(qtd=5000):
    e=_estado; alvo=min(TOTAL_CANDIDATOS,e["feito_250"]+int(qtd))
    while e["feito_250"]<alvo:
        jogo=gerar_jogo_ponderado(e["sd"]); e["feito_250"]+=1
        if jogo in e["vistos"]: continue
        e["vistos"].add(jogo); sc,car=score_jogo(jogo,e["ultimo"],e["sd"],e["hist"]); cand=(sc,jogo,car)
        if melhor(cand,e["campeao_250"]): e["campeao_250"]=cand
    pronto=e["feito_250"]>=TOTAL_CANDIDATOS
    return "%d|%d|%s"%(e["feito_250"],TOTAL_CANDIDATOS,"1" if pronto else "0")

def resultado_250():
    return bloco("JOGO 1 — CAMPEÃO DOS 250.000 SORTEADOS",_estado["campeao_250"])

def iniciar_universo():
    e=_estado; e["iter_universo"]=combinations(UNIVERSO,15); e["feito_universo"]=0; e["campeao_universo"]=None
    return "OK"

def passo_universo(qtd=20000):
    e=_estado; lote=list(islice(e["iter_universo"],int(qtd)))
    for jogo in lote:
        sc,car=score_jogo(jogo,e["ultimo"],e["sd"],e["hist"]); cand=(sc,jogo,car)
        if melhor(cand,e["campeao_universo"]): e["campeao_universo"]=cand
    e["feito_universo"]+=len(lote); pronto=len(lote)<int(qtd) or e["feito_universo"]>=TOTAL_UNIVERSO
    return "%d|%d|%s"%(e["feito_universo"],TOTAL_UNIVERSO,"1" if pronto else "0")

def resultado_final():
    e=_estado; nums=e["numeros"]
    cab="☘ AUTOFÁCIL\nLotofácil • jogo escolhido pelo sistema\n\nHistórico analisado: concursos %d até %d\nÚltimo resultado:\n%s"%(nums[0],nums[-1],fmt_jogo(e["ultimo"]))
    a=resultado_250(); b=bloco("JOGO 2 — CAMPEÃO DO UNIVERSO INTEIRO\n3.268.760 COMBINAÇÕES ANALISADAS",e["campeao_universo"])
    return cab+"\n\n================================================\n"+a+"\n\n================================================\n"+b+"\n\nConcluído."
