// Popup de mensagem
document.addEventListener("DOMContentLoaded", () => {
  const mensagemData = document.getElementById("mensagem-data");
  if (!mensagemData) return;

  const mensagem = mensagemData.dataset.mensagem;
  const tipo = mensagemData.dataset.tipo || "sucesso"; // Garante um valor padrão

  if (mensagem && mensagem.trim() !== "") {
    const popup = document.getElementById("popup");
    const texto = document.getElementById("popup-texto");

    texto.innerText = mensagem;

    // Remove classes antigas e adiciona a nova
    popup.classList.remove("popup--sucesso", "popup--erro", "popup--alerta");
    popup.classList.add(`popup--${tipo}`);

    popup.style.display = "block";
    setTimeout(() => {
      popup.style.display = "none";
      // Limpa a URL para evitar que o popup reapareça no refresh
      window.history.replaceState({}, document.title, window.location.pathname);
    }, 3000);
  }
});

// Função para atualizar campos de relatório
function atualizarCampos() {
  const tipo = document.getElementById("tipo-relatorio").value;
  document.getElementById("campo-periodo").style.display = "none";
  document.getElementById("campo-mesa").style.display = "none";

  if (tipo === "periodo") {
    document.getElementById("campo-periodo").style.display = "block";
  } else if (tipo === "mesa") {
    document.getElementById("campo-mesa").style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const popupRelatorio = document.getElementById("popup-relatorio");
  if (popupRelatorio) {
    popupRelatorio.style.display = "block";
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
