const $ = x => document.getElementById(x);

let savedItems = [];
let envs = [];


// --------------------------------------------------
// HELPERS
// --------------------------------------------------

function pretty(value) {
    try {
        return JSON.stringify(
            JSON.parse(value),
            null,
            2
        );
    } catch {
        return value;
    }
}


function formatAll() {

    $("headers").value =
        pretty($("headers").value);

    if ($("body").value.trim()) {
        $("body").value =
            pretty($("body").value);
    }
}


function parseHeaders() {

    const value =
        $("headers").value.trim();

    if (!value)
        return {};

    const headers =
        JSON.parse(value);

    if (
        !headers ||
        Array.isArray(headers) ||
        typeof headers !== "object"
    ) {
        throw Error(
            "Headers must be a JSON object"
        );
    }

    return headers;
}


function activeEnv() {

    if (!Array.isArray(envs))
        return {};

    const selected =
        $("envSelect").value;

    const environment =
        envs.find(
            e => e.name === selected
        );

    if (!environment)
        return {};

    try {

        return JSON.parse(
            environment.variables || "{}"
        );

    } catch {

        return {};
    }
}


function sizeOf(value) {

    try {

        return new Blob([
            typeof value === "string"
                ? value
                : JSON.stringify(value)
        ]).size;

    } catch {

        return 0;
    }
}


function esc(value) {

    return String(value).replace(
        /[&<>"']/g,
        m => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[m])
    );
}


// --------------------------------------------------
// SEND REQUEST
// --------------------------------------------------

async function send() {

    const url =
        $("url").value.trim();

    if (!url)
        return alert(
            "Enter a URL"
        );

    let headers;
    let body = null;

    try {

        headers = parseHeaders();

        const rawBody =
            $("body").value.trim();

        if (rawBody) {

            try {

                body =
                    JSON.parse(rawBody);

            } catch {

                body = rawBody;
            }
        }

    } catch (e) {

        return alert(
            e.message
        );
    }


    $("meta").textContent =
        "TRANSMITTING";

    $("pretty").textContent =
        "Sending request…";


    try {

        const response =
            await fetch(
                "/api/send",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        method:
                            $("method").value,

                        url,

                        headers,

                        body,

                        environment:
                            activeEnv()
                    })
                }
            );


        const data =
            await response.json();


        if (!data.success) {

            $("meta").textContent =
                "REQUEST ERROR";

            $("status").textContent =
                "ERR";

            $("pretty").textContent =
                JSON.stringify(
                    data,
                    null,
                    2
                );

            return;
        }


        $("meta").textContent =
            "COMPLETE";

        $("status").textContent =
            data.status_code +
            " " +
            data.reason;

        $("status").className =
            data.status_code < 400
                ? "ok"
                : "bad";

        $("time").textContent =
            data.response_time_ms +
            " ms";

        $("rtype").textContent =
            String(
                data.response_type ||
                ""
            ).toUpperCase();

        $("size").textContent =
            sizeOf(data.body) +
            " B";


        const text =
            typeof data.body === "string"
                ? data.body
                : JSON.stringify(
                    data.body,
                    null,
                    2
                );


        $("pretty").textContent =
            text;

        $("raw").textContent =
            typeof data.body === "string"
                ? data.body
                : JSON.stringify(
                    data.body
                );

        $("rh").textContent =
            JSON.stringify(
                data.headers || {},
                null,
                2
            );


        await loadHistory();


    } catch (e) {

        $("meta").textContent =
            "CLIENT ERROR";

        $("pretty").textContent =
            e.toString();
    }
}


// --------------------------------------------------
// SAVED REQUESTS
// --------------------------------------------------

async function save() {

    const name =
        prompt(
            "Collection name"
        );

    if (!name)
        return;


    try {

        const response =
            await fetch(
                "/api/saved",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        name,

                        method:
                            $("method").value,

                        url:
                            $("url").value,

                        headers:
                            parseHeaders(),

                        body:
                            $("body").value
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok ||
            !data.success) {

            throw Error(
                data.error ||
                "Unable to save request"
            );
        }


        await loadSaved();

        alert(
            "Saved to collection"
        );


    } catch (e) {

        alert(
            e.message
        );
    }
}


async function loadSaved() {

    try {

        const response =
            await fetch(
                "/api/saved"
            );

        const data =
            await response.json();


        savedItems =
            Array.isArray(data)
                ? data
                : Array.isArray(
                    data.saved_requests
                )
                    ? data.saved_requests
                    : [];


        $("savedCount").textContent =
            savedItems.length;


        if (!$("savedList"))
            return;


        $("savedList").innerHTML =
            savedItems.length

                ? savedItems.map(
                    x =>
                        `<div class="listitem">
                            <div class="li-main">
                                <b>${esc(x.name)}</b>
                                <small>
                                    ${esc(x.method)}
                                    ·
                                    ${esc(x.url)}
                                </small>
                            </div>

                            <div class="li-actions">
                                <button onclick="useSaved(${x.id})">
                                    USE
                                </button>

                                <button onclick="delSaved(${x.id})">
                                    ×
                                </button>
                            </div>
                        </div>`
                ).join("")

                : "<div class=empty>No saved requests.</div>";


    } catch (e) {

        console.error(
            "Saved loading failed:",
            e
        );

        savedItems = [];

        $("savedCount").textContent =
            "0";

        if ($("savedList")) {

            $("savedList").innerHTML =
                "<div class=empty>Unable to load saved requests.</div>";
        }
    }
}


function useSaved(id) {

    const item =
        savedItems.find(
            x => x.id === id
        );

    if (!item)
        return;


    $("method").value =
        item.method || "GET";

    $("url").value =
        item.url || "";

    $("headers").value =
        pretty(
            item.headers || "{}"
        );

    $("body").value =
        item.body || "";


    view(
        "tester",
        document.querySelector(".nav")
    );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


async function delSaved(id) {

    try {

        await fetch(
            "/api/saved/" + id,
            {
                method: "DELETE"
            }
        );

        await loadSaved();

    } catch (e) {

        alert(
            e.message
        );
    }
}


// --------------------------------------------------
// HISTORY
// --------------------------------------------------

async function loadHistory() {

    try {

        const response =
            await fetch(
                "/api/history"
            );

        const data =
            await response.json();


        const history =
            Array.isArray(data)
                ? data
                : Array.isArray(
                    data.history
                )
                    ? data.history
                    : [];


        $("historyCount").textContent =
            history.length;


        $("historyList").innerHTML =
            history.length

                ? history.map(
                    x =>
                        `<div class="listitem">
                            <div class="li-main">
                                <b>
                                    ${esc(x.method)}
                                    ·
                                    ${esc(x.status)}
                                </b>

                                <small>
                                    ${esc(x.url)}
                                </small>
                            </div>

                            <div>
                                ${esc(x.ms)} ms
                            </div>
                        </div>`
                ).join("")

                : "<div class=empty>No request history.</div>";


    } catch (e) {

        console.error(
            "History loading failed:",
            e
        );

        $("historyCount").textContent =
            "0";

        $("historyList").innerHTML =
            "<div class=empty>Unable to load request history.</div>";
    }
}


async function clearHistory() {

    try {

        const response =
            await fetch(
                "/api/history",
                {
                    method: "DELETE"
                }
            );

        const data =
            await response.json();


        if (!response.ok ||
            !data.success) {

            throw Error(
                data.error ||
                "Unable to clear history"
            );
        }


        await loadHistory();


    } catch (e) {

        alert(
            e.message
        );
    }
}


// --------------------------------------------------
// ENVIRONMENTS
// --------------------------------------------------

async function loadEnv() {

    try {

        const response =
            await fetch(
                "/api/env"
            );

        const data =
            await response.json();


        envs =
            Array.isArray(data)

                ? data

                : Array.isArray(
                    data.environments
                )

                    ? data.environments

                    : [];


        $("envSelect").innerHTML =
            '<option value="">No environment</option>' +

            envs.map(
                x =>
                    `<option value="${esc(x.name)}">
                        ${esc(x.name)}
                    </option>`
            ).join("");


        $("envList").innerHTML =
            envs.length

                ? envs.map(
                    x => {

                        let variables = {};

                        try {

                            variables =
                                JSON.parse(
                                    x.variables ||
                                    "{}"
                                );

                        } catch {}


                        return `
                            <div class="envrow">
                                <b>
                                    ${esc(x.name)}
                                </b>
                                ·
                                ${Object.keys(
                                    variables
                                ).map(esc).join(", ")}
                            </div>
                        `;
                    }
                ).join("")

                : "<div class=empty>No environments yet.</div>";


    } catch (e) {

        console.error(
            "Environment loading failed:",
            e
        );

        envs = [];


        $("envSelect").innerHTML =
            '<option value="">No environment</option>';


        $("envList").innerHTML =
            "<div class=empty>Unable to load environments.</div>";
    }
}


async function saveEnv() {

    const name =
        $("envName").value.trim();

    if (!name)
        return alert(
            "Environment name required"
        );


    try {

        const variables =
            JSON.parse(
                $("envVars").value ||
                "{}"
            );


        if (
            !variables ||
            Array.isArray(variables) ||
            typeof variables !== "object"
        ) {

            throw Error(
                "Variables must be a JSON object"
            );
        }


        const response =
            await fetch(
                "/api/env",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        name,
                        variables
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok ||
            !data.success) {

            throw Error(
                data.error ||
                "Unable to save environment"
            );
        }


        $("envName").value =
            "";

        $("envVars").value =
            "";


        await loadEnv();


    } catch (e) {

        alert(
            e.message ||
            "Invalid JSON"
        );
    }
}


// --------------------------------------------------
// CURL
// --------------------------------------------------

function copyCurl() {

    const url =
        $("url").value;

    let headers = {};

    try {

        headers =
            parseHeaders();

    } catch (e) {

        return alert(
            e.message
        );
    }


    let curl =
        `curl -X ${$("method").value} ${JSON.stringify(url)}`;


    Object.entries(
        headers
    ).forEach(
        ([key, value]) => {

            curl +=
                ` -H ${JSON.stringify(
                    key + ": " + value
                )}`;
        }
    );


    const body =
        $("body").value.trim();


    if (body) {

        curl +=
            ` --data ${JSON.stringify(body)}`;
    }


    if (
        navigator.clipboard &&
        navigator.clipboard.writeText
    ) {

        navigator.clipboard.writeText(
            curl
        );
    }


    alert(curl);
}


function generateCurl() {
    copyCurl();
}


// --------------------------------------------------
// RESPONSE
// --------------------------------------------------

function decodeResponse() {

    view(
        "tester",
        document.querySelector(".nav")
    );

    $("pretty").focus();
}


// --------------------------------------------------
// RESET
// --------------------------------------------------

function resetReq() {

    $("url").value =
        "";

    $("headers").value =
        "{}";

    $("body").value =
        "";

    $("pretty").textContent =
        "Fire a request to inspect the response.";

    $("raw").textContent =
        "";

    $("rh").textContent =
        "";

    $("status").textContent =
        "—";

    $("time").textContent =
        "—";

    $("rtype").textContent =
        "—";

    $("size").textContent =
        "—";

    $("meta").textContent =
        "STANDBY";
}


// --------------------------------------------------
// TABS
// --------------------------------------------------

function tab(id, button) {

    [
        "pretty",
        "raw",
        "rh"
    ].forEach(
        x =>
            $(x).classList.add(
                "hidden"
            )
    );


    $(id).classList.remove(
        "hidden"
    );


    document
        .querySelectorAll(".tab")
        .forEach(
            x =>
                x.classList.remove(
                    "active"
                )
        );


    button.classList.add(
        "active"
    );
}


// --------------------------------------------------
// VIEWS
// --------------------------------------------------

function view(id, button) {

    document
        .querySelectorAll(".screen")
        .forEach(
            x =>
                x.classList.remove(
                    "active"
                )
        );


    const screen =
        $(id);

    if (screen) {

        screen.classList.add(
            "active"
        );
    }


    document
        .querySelectorAll(".nav")
        .forEach(
            x =>
                x.classList.remove(
                    "active"
                )
        );


    if (button) {

        button.classList.add(
            "active"
        );
    }


    if (id === "history") {

        loadHistory();
    }


    if (id === "saved") {

        loadSaved();
    }


    if (id === "env") {

        loadEnv();
    }
}


// --------------------------------------------------
// STARTUP
// --------------------------------------------------

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadSaved();
        loadHistory();
        loadEnv();

    }
);
