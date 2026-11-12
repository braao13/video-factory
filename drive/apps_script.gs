/**
 * Ponte video-factory -> Google Drive.
 * Publicar como App da Web: Executar como "Eu", Acesso "Qualquer pessoa".
 * Em Configuracoes do projeto > Propriedades do script, criar CHAVE = <senha longa>.
 * O Claude chama este endpoint pra listar as pastas e abrir uma sessao de upload;
 * os bytes do video vao direto pro Google (upload resumable), sem passar pelo chat.
 */
const PASTAS = {
  editados: '1lysKpa2762Y8yH62wyAndWE1540rSAoA',
  originais: '1zwuitr0BKm3B3z6-fLU1H9zuhUGY7T9b',
  modelos: '1bIGHwwiBI9ipWGNByOINC7E0YULueQNa',
};

function doPost(e) {
  const b = JSON.parse(e.postData.contents);
  const chave = PropertiesService.getScriptProperties().getProperty('CHAVE');
  if (!chave || b.chave !== chave) return saida({erro: 'chave invalida'});

  if (b.acao === 'listar') {
    const r = {};
    Object.keys(PASTAS).forEach((k) => {
      r[k] = [];
      const it = DriveApp.getFolderById(PASTAS[k]).getFiles();
      while (it.hasNext()) {
        const f = it.next();
        if (!f.isTrashed()) r[k].push({id: f.getId(), nome: f.getName(), tamanho: f.getSize()});
      }
    });
    return saida(r);
  }

  if (b.acao === 'sessao') {
    if (!PASTAS[b.pasta]) return saida({erro: 'pasta invalida'});
    const resp = UrlFetchApp.fetch(
      'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&supportsAllDrives=true', {
        method: 'post',
        contentType: 'application/json; charset=UTF-8',
        headers: {
          Authorization: 'Bearer ' + ScriptApp.getOAuthToken(),
          'X-Upload-Content-Type': b.mime || 'video/mp4',
          'X-Upload-Content-Length': String(b.tamanho),
        },
        payload: JSON.stringify({name: b.nome, parents: [PASTAS[b.pasta]]}),
        muteHttpExceptions: true,
      });
    const h = resp.getAllHeaders();
    return saida({url: h['Location'] || h['location'] || null, status: resp.getResponseCode(), corpo: resp.getContentText()});
  }

  if (b.acao === 'lixeira') {
    DriveApp.getFileById(b.id).setTrashed(true);
    return saida({ok: true});
  }
  return saida({erro: 'acao desconhecida'});
}

function saida(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

// Rode esta funcao 1x no editor pra autorizar Drive + chamadas externas.
function autorizar() {
  DriveApp.getFolderById(PASTAS.editados).getName();
  UrlFetchApp.fetch('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest');
}
