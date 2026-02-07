// -- PSEUDO --
let pseudo = localStorage.getItem("pseudo") || ("Player" + Math.floor(Math.random() * 1000));
localStorage.setItem("pseudo", pseudo);
document.getElementById("pPseudo").textContent = "Bonjour " + pseudo;

// -- WebSocket --
let host = window.location.hostname;
let wsUrl = "ws://" + host + ":8081/ws";
let ws = new WebSocket(wsUrl);

ws.onopen = () => console.log("WebSocket connecté!");

ws.onmessage = e => {
  const data = JSON.parse(e.data);
  console.log("Reçu :", data);
  if (data.type === "assign_id" && data.player_id) {
    document.getElementById("pPseudo")
        .textContent = `Bonjour Player ${data.player_id}`;
    // stocker dans une var si besoin pour envoyer MOVE/AIM plus tard
    window._myPlayerId = data.player_id;
  }
};
ws.onclose = () => console.log("WebSocket fermé.");
ws.onerror = (err) => console.error("WS erreur:", err);

// === JOYSTICK DÉPLACEMENT ===
const joyMove = document.getElementById("joystickMove");
const innerMove = document.getElementById("innerMove");

let movePointerId = null;
let moveCenter = { x:0, y:0 };
let moveVector = { x:0, y:0 };

// calcule le centre absolu
function getCenter(el) {
  let rect = el.getBoundingClientRect();
  return {
    x: rect.left + rect.width/2,
    y: rect.top + rect.height/2
  };
}

function pointerDownMove(e) {
  if (movePointerId === null) {
    movePointerId = e.pointerId;
    moveCenter = getCenter(joyMove);
  }
}
function pointerMoveMove(e) {
  if (e.pointerId !== movePointerId) return;
  let dx = e.clientX - moveCenter.x;
  let dy = e.clientY - moveCenter.y;
  let r = joyMove.offsetWidth/2 - 25;
  let dist = Math.sqrt(dx*dx + dy*dy);
  if (dist > r) {
    dx = (dx/dist)*r;
    dy = (dy/dist)*r;
  }
  innerMove.style.transform = `translate(${dx}px, ${dy}px)`;

  // vecteur normalisé
  if (dist < 10) {
    moveVector.x = 0;
    moveVector.y = 0;
  } else {
    let mag = dist / r;
    let nx = dx/dist;
    let ny = dy/dist;
    moveVector.x = nx * mag; // entre -1 et 1
    moveVector.y = ny * mag;
  }
}
function pointerUpMove(e) {
  if (e.pointerId !== movePointerId) return;
  movePointerId = null;
  moveVector.x = 0;
  moveVector.y = 0;
  innerMove.style.transform = "translate(-50%, -50%)";
}

// Envoi périodique du vecteur move
function sendMoveVector() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    let msg = {
      pseudo,
      command: "MOVE_VECTOR",
      dx: moveVector.x,
      dy: moveVector.y
    };
    ws.send(JSON.stringify(msg));
  }
}

joyMove.addEventListener("pointerdown", pointerDownMove);
joyMove.addEventListener("pointermove", pointerMoveMove);
joyMove.addEventListener("pointerup", pointerUpMove);
joyMove.addEventListener("pointercancel", pointerUpMove);
joyMove.addEventListener("pointerleave", pointerUpMove);

setInterval(sendMoveVector, 50);


// === JOYSTICK VISÉE ===
const joyAim = document.getElementById("joystickAim");
const innerAim = document.getElementById("innerAim");

let aimPointerId = null;
let aimCenter = { x:0, y:0 };
let aimVector = { x:0, y:0 };

function pointerDownAim(e) {
  if (aimPointerId === null) {
    aimPointerId = e.pointerId;
    aimCenter = getCenter(joyAim);
  }
}
function pointerMoveAim(e) {
  if (e.pointerId !== aimPointerId) return;
  let dx = e.clientX - aimCenter.x;
  let dy = e.clientY - aimCenter.y;
  let r = joyAim.offsetWidth/2 - 25;
  let dist = Math.sqrt(dx*dx + dy*dy);
  if (dist > r) {
    dx = (dx/dist)*r;
    dy = (dy/dist)*r;
  }
  innerAim.style.transform = `translate(${dx}px, ${dy}px)`;

  aimVector.x = dx;
  aimVector.y = dy;

  // On envoie AIM_VECTOR en continu pour que le serveur calcule aim_angle
  if (ws && ws.readyState === WebSocket.OPEN) {
    let msg = {
      pseudo,
      command: "AIM_VECTOR",
      dx: dx,
      dy: dy
    };
    ws.send(JSON.stringify(msg));
  }
}
function pointerUpAim(e) {
  if (e.pointerId !== aimPointerId) return;
  aimPointerId = null;
  innerAim.style.transform = "translate(-50%, -50%)";

  let dx = aimVector.x;
  let dy = aimVector.y;
  let dist = Math.sqrt(dx*dx + dy*dy);
  if (dist > 20) {
    let angle = Math.atan2(dy, dx);
    if (ws && ws.readyState === WebSocket.OPEN) {
      let msg = {
        pseudo,
        command: "SHOOT_ANGLE",
        angle: angle
      };
      ws.send(JSON.stringify(msg));
    }
  }
  // reset
  aimVector.x = 0;
  aimVector.y = 0;
}

joyAim.addEventListener("pointerdown", pointerDownAim);
joyAim.addEventListener("pointermove", pointerMoveAim);
joyAim.addEventListener("pointerup", pointerUpAim);
joyAim.addEventListener("pointercancel", pointerUpAim);
joyAim.addEventListener("pointerleave", pointerUpAim);