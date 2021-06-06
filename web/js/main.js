document.getElementById("button-new_inform_slot").addEventListener("click", ()=>{eel.new_inform_slot()}, false);
document.getElementById("button-new_request_slot").addEventListener("click", ()=>{eel.new_request_slot()}, false);
document.getElementById("button-send").addEventListener("click", ()=>{eel.send()}, false);
document.getElementById("button-clear").addEventListener("click", ()=>{eel.clear_all_slots()}, false);
document.getElementById("button-end").addEventListener("click", ()=>{eel.end_conversation()}, false);

var entity_inform_idx;
var entity_request_idx;

eel.expose(get_dialog_config);
function get_dialog_config(intent){
    console.log(intent);

    intent.forEach(element => {
        var x = document.getElementById("intents");
        var option = document.createElement("option");
        option.text = element;
        option.value = element;
        x.add(option);
    });

    entity_inform_idx = 0;
    entity_request_idx = 0;
}

eel.expose(new_inform_slot);
function new_inform_slot(intent) {
    console.log(entity_inform_idx);
    var x = document.getElementById("inform_slots");

    var newlabel = document.createElement("Label");
    var text = "inform_entity" + entity_inform_idx.toString();
    console.log(text);
    newlabel.setAttribute("for", text);
    newlabel.innerHTML = "Entity: ";
    x.appendChild(newlabel);

    console.log(intent);
    var newselect = document.createElement("Select");
    newselect.setAttribute("id", text);
    intent.forEach(element => {
        var option = document.createElement("option");
        option.text = element;
        option.value = element;
        newselect.add(option);
    });
    x.appendChild(newselect);

    var newlabel = document.createElement("Label");
    var text = "inform_value" + entity_inform_idx.toString();
    newlabel.setAttribute("for", text);
    newlabel.innerHTML = " Value (default: anything): ";
    x.appendChild(newlabel);

    var newinput = document.createElement("Input");
    newinput.setAttribute("id", text);
    newinput.setAttribute("name", text);
    newinput.setAttribute("type", "text");
    x.appendChild(newinput);

    lineBreak = document.createElement('br');
    x.appendChild(lineBreak);

    entity_inform_idx = entity_inform_idx + 1;
}

eel.expose(new_request_slot);
function new_request_slot(intent) {
    console.log(entity_request_idx);
    var x = document.getElementById("request_slots");

    var newlabel = document.createElement("Label");
    var text = "request_entity" + entity_request_idx.toString();
    newlabel.setAttribute("for", text);
    newlabel.innerHTML = "Entity: ";
    x.appendChild(newlabel);

    console.log(intent);
    var newselect = document.createElement("Select");
    newselect.setAttribute("id", text);
    intent.forEach(element => {
        var option = document.createElement("option");
        option.text = element;
        option.value = element;
        newselect.add(option);
    });
    x.appendChild(newselect);

    lineBreak = document.createElement('br');
    x.appendChild(lineBreak);

    entity_request_idx = entity_request_idx + 1;
}

function get_nl() {
    return document.getElementById("nl").value;
}

function get_intent() {
    var x = document.getElementById("intents");
    var value = x.value;
    return value;
}

function get_inform_slots() {
    var inform_slots = {};
    var x = document.getElementById("inform_slots");
    if (x.length > 0) {
        for (var i = 0; i < entity_inform_idx; i++) {
            console.log(i);
            var id_entity = "inform_entity" + i.toString();
            var entity = document.getElementById(id_entity).value;
            console.log(entity);
            var id_val = "inform_value" + i.toString();
            var val = document.getElementById(id_val).value;
            console.log(val);
            if (val == "") val = "anything";
            inform_slots[entity] = val;
            console.log(inform_slots);
        }
    }
    else {
        console.log("none");
    }
    return inform_slots;
}

function get_request_slots() {
    var request_slots = {};
    var x = document.getElementById("request_slots");
    if (x.length > 0) {
        for (var i = 0; i < entity_request_idx; i++) {
            console.log(i);
            var id_entity = "request_entity" + i.toString();
            var entity = document.getElementById(id_entity).value;
            console.log(entity);
            request_slots[entity] = "UNK";
            console.log(request_slots);
        }
    }
    else {
        console.log("none");
    }
    return request_slots;
}

eel.expose(clear_all_slots);
function clear_all_slots() {
    var x = document.getElementById("nl");
    x.value = '';
    var x = document.getElementById("inform_slots");
    while (x.firstChild) {
        x.removeChild(x.firstChild);
    }
    var y = document.getElementById("request_slots");
    while (y.firstChild) {
        y.removeChild(y.firstChild);
    }
    entity_inform_idx = 0;
    entity_request_idx = 0;
}

eel.expose(send);
function send() {
    var nl = get_nl();
    var user_action;
    if (nl == "") {
        user_action = {}
        user_action.intent = get_intent();
        user_action.inform_slots = get_inform_slots();
        user_action.request_slots = get_request_slots();
    }
    else {
        user_action = nl;
    }
    console.log(user_action);
    clear_all_slots();
    return user_action;
}

eel.expose(update_dialog);
function update_dialog(action) {
    var x = document.getElementById("dialog");
    x.innerHTML = x.innerHTML + action + "<br>";
}

eel.expose(clear_dialog);
function clear_dialog() {
    var x = document.getElementById("dialog");
    x.innerHTML = "";
}
