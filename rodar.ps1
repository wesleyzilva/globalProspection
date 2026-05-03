﻿#Requires -Version 5.1
<#
.SYNOPSIS
    Menu interativo para rodar o Global Prospection.
.USAGE
    cd C:\repositorio\globalProspection
    .\rodar.ps1
#>

Set-Location $PSScriptRoot
$ErrorActionPreference = 'Continue'

$VERTICALS = @(
    'Fintech', 'TradeTech', 'HealthTech', 'CXTech',
    'SalesTech', 'LegalTech', 'AIGovernance', 'Cybersecurity', 'Platform'
)

function Write-Header {
    param([string]$Text)
    $line = '=' * ($Text.Length + 4)
    Write-Host ''
    Write-Host "+$line+" -ForegroundColor Cyan
    Write-Host "|  $Text  |" -ForegroundColor Cyan
    Write-Host "+$line+" -ForegroundColor Cyan
    Write-Host ''
}

function Show-Menu {
    Clear-Host
    Write-Header 'GLOBAL PROSPECTION'

    Write-Host '  [1]  Rodar com Hunter.io  (FREE  25 buscas/mes)' -ForegroundColor Green
    Write-Host '  [2]  Rodar com Snov.io    (FREE 1000 creditos/mes) *** RECOMENDADO ***' -ForegroundColor Green
    Write-Host '  [3]  Rodar com Apollo.io  (FREE  50 creditos/mes — plano pago p/ busca)' -ForegroundColor DarkGray
    Write-Host '  [4]  Rodar combinado      (Snov emails + Apollo nomes)' -ForegroundColor Yellow
    Write-Host ''
    Write-Host '  [5]  Ver lista final de contatos (prospects_final.csv)' -ForegroundColor Cyan
    Write-Host '  [6]  Ver relatorio de campanhas' -ForegroundColor White
    Write-Host '  [7]  Abrir pasta de resultados (CSV)' -ForegroundColor White
    Write-Host ''
    Write-Host '  [8]  Prospecção LOCAL (Lecto.com.br)  → para aquecimento via WhatsApp' -ForegroundColor Magenta
    Write-Host ''
    Write-Host '  [0]  Sair' -ForegroundColor DarkGray
    Write-Host ''
}

function Select-Verticals {
    Write-Host '  Verticais disponiveis:' -ForegroundColor Cyan
    for ($i = 0; $i -lt $VERTICALS.Count; $i++) {
        Write-Host ("  [{0,2}] {1}" -f ($i + 1), $VERTICALS[$i]) -ForegroundColor White
    }
    Write-Host ''
    Write-Host '  Digite os numeros separados por espaco (Enter = TODAS):' -ForegroundColor Yellow
    $input = Read-Host '  Verticais'

    if ([string]::IsNullOrWhiteSpace($input)) { return @() }

    $selected = @()
    foreach ($n in ($input -split '\s+')) {
        $idx = [int]$n - 1
        if ($idx -ge 0 -and $idx -lt $VERTICALS.Count) {
            $selected += $VERTICALS[$idx]
        }
    }
    return $selected
}

function Ask-Max {
    $val = Read-Host '  Limite de empresas (Enter = sem limite)'
    if ([string]::IsNullOrWhiteSpace($val)) { return $null }
    return $val.Trim()
}

function Ask-Campaign {
    $ts  = (Get-Date -Format 'yyyyMMdd_HHmm')
    $val = Read-Host "  Prefixo do nome da campanha (Enter = automatico)"
    if ([string]::IsNullOrWhiteSpace($val)) { return $null }
    # sempre adiciona timestamp para evitar reuso de dedup
    return "$($val.Trim())_$ts"
}

function Build-Args {
    param([string]$Source)

    $args = @('run.py', '--source', $Source)

    $verticals = Select-Verticals
    if ($verticals.Count -gt 0) {
        $args += '--verticals'
        $args += $verticals
    }

    $max = Ask-Max
    if ($max) { $args += @('--max', $max) }

    $campaign = Ask-Campaign
    if ($campaign) { $args += @('--campaign', $campaign) }

    return $args
}

function Show-FinalCSV {
    $finalPath = Join-Path $PSScriptRoot 'output\prospects_final.csv'
    if (-not (Test-Path $finalPath)) {
        Write-Host '  Nenhum contato ainda. Rode uma campanha primeiro.' -ForegroundColor Yellow
        return
    }

    $rows = Import-Csv $finalPath -Encoding UTF8
    $total = $rows.Count

    if ($total -eq 0) {
        Write-Host '  Lista final vazia — as campanhas nao retornaram contatos.' -ForegroundColor Yellow
        return
    }

    Write-Host ''
    Write-Host ("  " + ("-" * 80)) -ForegroundColor DarkGray
    Write-Host "  LISTA FINAL — prospects_final.csv   ($total contatos unicos)" -ForegroundColor Cyan
    Write-Host ("  " + ("-" * 80)) -ForegroundColor DarkGray
    Write-Host ''

    # cabecalho
    Write-Host ('  {0,-22} {1,-14} {2,-22} {3,-28} {4}' -f
        'EMPRESA', 'VERTICAL', 'NOME', 'CARGO', 'EMAIL') -ForegroundColor Yellow
    Write-Host ('  ' + ('-' * 100)) -ForegroundColor DarkGray

    foreach ($r in $rows) {
        $nome  = "$($r.primeiro_nome) $($r.ultimo_nome)".Trim()
        $email = if ($r.email) { $r.email } else { '(sem email)' }
        Write-Host ('  {0,-22} {1,-14} {2,-22} {3,-28} {4}' -f
            $r.empresa, $r.vertical, $nome, $r.cargo, $email)
    }

    Write-Host ''
    Write-Host "  Total: $total contatos | Arquivo: output\prospects_final.csv" -ForegroundColor Green
}

function Show-SnovBalance {
    Write-Host '  Verificando saldo Snov.io...' -ForegroundColor DarkGray
    python -c @"
import os; from dotenv import load_dotenv; load_dotenv()
from src.snov_client import SnovClient
try:
    b = SnovClient().check_balance()
    bal   = b.get('balance', '?')
    reset = b.get('limit_resets_in', '?')
    exp   = b.get('expires_in', '?')
    print(f'  Creditos disponiveis : {bal}')
    print(f'  Reset do limite em   : {reset} dias')
    print(f'  Assinatura expira em : {exp} dias')
except Exception as e:
    print(f'  [Aviso] Nao foi possivel verificar saldo: {e}')
"@
    Write-Host ''
}

function Run-Campaign {
    param([string]$Source)

    Write-Host ''
    Write-Host "  Fonte: $Source" -ForegroundColor Cyan
    Write-Host ''

    if ($Source -in @('snov', 'combined')) {
        Show-SnovBalance
    }

    $pyArgs = Build-Args -Source $Source

    Write-Host ''
    Write-Host '  Executando: python ' ($pyArgs -join ' ') -ForegroundColor DarkGray
    Write-Host ''

    python @pyArgs

    # exibe resumo da lista final automaticamente apos cada campanha
    Write-Host ''
    Show-FinalCSV
}

function Show-LocalCSV {
    $localDir = Join-Path $PSScriptRoot 'output\local'
    $finalPath = Join-Path $localDir 'prospects_local_final.csv'

    if (-not (Test-Path $finalPath)) {
        Write-Host '  Nenhum contato local ainda. Rode a prospecao local primeiro.' -ForegroundColor Yellow
        return
    }

    $rows  = Import-Csv $finalPath -Encoding UTF8
    $total = $rows.Count

    if ($total -eq 0) {
        Write-Host '  Lista local vazia.' -ForegroundColor Yellow
        return
    }

    Write-Host ''
    Write-Host ("  " + ("-" * 80)) -ForegroundColor DarkGray
    Write-Host "  LISTA LOCAL — prospects_local_final.csv   ($total contatos)" -ForegroundColor Cyan
    Write-Host ("  " + ("-" * 80)) -ForegroundColor DarkGray
    Write-Host ''

    Write-Host ('  {0,-28} {1,-16} {2,-16} {3,-20} {4}' -f
        'EMPRESA', 'CIDADE', 'WHATSAPP', 'TELEFONE', 'EMAIL') -ForegroundColor Yellow
    Write-Host ('  ' + ('-' * 100)) -ForegroundColor DarkGray

    foreach ($r in $rows) {
        $wapp  = if ($r.whatsapp)     { $r.whatsapp }     else { '—' }
        $tel   = if ($r.telefone_fixo) { $r.telefone_fixo } else { '—' }
        $email = if ($r.email)         { $r.email }         else { '—' }
        Write-Host ('  {0,-28} {1,-16} {2,-16} {3,-20} {4}' -f
            $r.nome_empresa, $r.cidade_estado, $wapp, $tel, $email)
    }

    Write-Host ''
    Write-Host "  Total: $total contatos | Arquivo: output\local\prospects_local_final.csv" -ForegroundColor Green
}

function Run-Local {
    Write-Host ''
    Write-Header 'PROSPECÇÃO LOCAL — Lecto.com.br'
    Write-Host '  Busca empresas/estabelecimentos em uma cidade para'
    Write-Host '  aquecimento de leads via WhatsApp.' -ForegroundColor DarkGray
    Write-Host ''

    $cidade = Read-Host '  Cidade para buscar (ex: sao carlos)'
    if ([string]::IsNullOrWhiteSpace($cidade)) {
        Write-Host '  Cidade obrigatoria.' -ForegroundColor Red
        return
    }

    Write-Host ''
    Write-Host '  Segmentos sugeridos: todas-as-cidades, advocacia, odontologia,' -ForegroundColor DarkGray
    Write-Host '                       academia, restaurante, clinica, estetica, ...' -ForegroundColor DarkGray
    $keyword = Read-Host '  Segmento/keyword (Enter = todas-as-cidades)'
    if ([string]::IsNullOrWhiteSpace($keyword)) { $keyword = 'todas-as-cidades' }

    $maxVal = Read-Host '  Maximo de resultados (Enter = 100)'
    if ([string]::IsNullOrWhiteSpace($maxVal)) { $maxVal = '100' }

    Write-Host ''
    Write-Host "  Iniciando scraper: cidade='$cidade' keyword='$keyword' max=$maxVal" -ForegroundColor DarkGray
    Write-Host ''

    python run_local.py --cidade $cidade --keyword $keyword --max $maxVal

    Write-Host ''
    Show-LocalCSV

    $localDir = Join-Path $PSScriptRoot 'output\local'
    if (Test-Path $localDir) {
        $abrir = Read-Host '  Abrir pasta output\local? (s/N)'
        if ($abrir -match '^[sS]') { Invoke-Item $localDir }
    }
}

# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------
while ($true) {
    Show-Menu
    $opcao = Read-Host '  Escolha uma opcao'
    Write-Host ''

    switch ($opcao.Trim()) {
        '1' { Run-Campaign -Source 'hunter'   }
        '2' { Run-Campaign -Source 'snov'     }
        '3' { Run-Campaign -Source 'apollo'   }
        '4' { Run-Campaign -Source 'combined' }
        '5' { Show-FinalCSV }
        '6' {
            Write-Host '  Relatorio geral de campanhas:' -ForegroundColor Cyan
            python run.py --report
        }
        '7' {
            $csvDir = Join-Path $PSScriptRoot 'output\campaigns'
            if (Test-Path $csvDir) {
                Invoke-Item $csvDir
            } else {
                Write-Host '  Nenhuma campanha rodada ainda.' -ForegroundColor Yellow
            }
        }
        '8' { Run-Local }
        '0' { Write-Host "`n  Ate logo!`n" -ForegroundColor Cyan; exit 0 }
        default { Write-Host '  Opcao invalida.' -ForegroundColor Red }
    }

    Write-Host ''
    Read-Host '  Pressione Enter para voltar ao menu'
}
