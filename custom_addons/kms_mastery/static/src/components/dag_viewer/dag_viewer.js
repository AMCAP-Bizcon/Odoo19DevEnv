/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { cookie } from "@web/core/browser/cookie";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

/**
 * DAG Viewer OWL Component
 *
 * Renders knowledge nodes as an interactive force-directed graph.
 * Nodes are color-coded by user mastery state:
 *   - Grey: locked
 *   - Blue: unlocked
 *   - Green: mastered
 *
 * Clicking a node navigates to its form view.
 */
export class DagViewer extends Component {
    static template = "kms_mastery.DagViewer";
    static props = {
        ...standardActionServiceProps,
        courseId: { type: Number, optional: true },
    };

    setup() {
        this.canvasRef = useRef("dagCanvas");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            nodes: [],
            edges: [],
            loading: true,
        });

        // Simulation state
        this.simNodes = [];
        this.simEdges = [];
        this.animFrame = null;
        this.dragging = null;
        this.offset = { x: 0, y: 0 };
        this.scale = 1;
        this.pan = { x: 0, y: 0 };
        this.lastMouse = { x: 0, y: 0 };
        this.isPanning = false;

        onMounted(() => this._init());
        onWillUnmount(() => this._cleanup());
    }

    get courseId() {
        return (
            this.props.courseId ||
            this.props.action?.context?.active_id ||
            this.props.action?.params?.courseId ||
            this.props.action?.context?.default_course_id ||
            null
        );
    }

    get isMyNodesOnly() {
        return Boolean(
            this.props.action?.params?.my_nodes_only ||
            this.props.action?.context?.my_nodes_only
        );
    }

    get title() {
        if (this.props.action?.name) {
            return this.props.action.name;
        }
        return this.isMyNodesOnly ? "My Knowledge DAG" : "Knowledge DAG";
    }

    async _init() {
        await this._loadData();
        this._initSimulation();
        this._startAnimation();
        this._attachEvents();
    }

    _cleanup() {
        if (this.animFrame) {
            cancelAnimationFrame(this.animFrame);
        }
    }

    async _loadData() {
        const courseId = this.courseId;
        const isMyNodesOnly = this.isMyNodesOnly;
        let nodeDomain = [];

        if (courseId) {
            const courseNodeIds = await this._getCourseNodeIds(courseId);
            nodeDomain = [["id", "in", courseNodeIds]];
        } else if (isMyNodesOnly) {
            const uid = this._getCurrentUserId();
            const userCourses = await this.orm.searchRead(
                "kms.course",
                ["|", ["learner_ids", "in", uid], ["instructor_id", "=", uid]],
                ["node_ids"]
            );
            const myNodeIds = [...new Set(userCourses.flatMap((c) => c.node_ids))];
            nodeDomain = [["id", "in", myNodeIds]];
        }

        // Load nodes
        const nodes = await this.orm.searchRead(
            "kms.node",
            nodeDomain,
            ["id", "name", "prerequisite_ids", "dependent_ids"]
        );

        // Load user progress for current user
        const userNodes = await this.orm.searchRead(
            "kms.user.node",
            [["user_id", "=", this._getCurrentUserId()]],
            ["node_id", "state"]
        );

        const stateMap = {};
        for (const un of userNodes) {
            stateMap[un.node_id[0]] = un.state;
        }

        // Build node and edge data
        const nodeIds = new Set(nodes.map((n) => n.id));
        const nodeData = nodes.map((n, i) => ({
            id: n.id,
            name: n.name,
            state: stateMap[n.id] || "locked",
            prerequisite_ids: n.prerequisite_ids,
            // Initial position: spread in a grid
            x: 150 + (i % 4) * 200,
            y: 100 + Math.floor(i / 4) * 150,
            vx: 0,
            vy: 0,
            fx: null,
            fy: null,
        }));

        const edgeData = [];
        for (const node of nodes) {
            for (const prereqId of node.prerequisite_ids) {
                if (nodeIds.has(prereqId)) {
                    edgeData.push({
                        source: prereqId,
                        target: node.id,
                    });
                }
            }
        }

        this.simNodes = nodeData;
        this.simEdges = edgeData;

        this.state.nodes = nodeData;
        this.state.edges = edgeData;
        this.state.loading = false;
    }

    async _getCourseNodeIds(courseId) {
        const courses = await this.orm.read(
            "kms.course",
            [courseId],
            ["node_ids"]
        );
        return courses.length ? courses[0].node_ids : [];
    }

    _getCurrentUserId() {
        return user.userId || odoo.session_info?.uid || 0;
    }

    _initSimulation() {
        // Simple force-directed layout
        // Apply topological ordering first for better initial layout
        this._topologicalLayout();
    }

    _topologicalLayout() {
        const nodes = this.simNodes;
        const edges = this.simEdges;

        if (!nodes.length) return;

        // Build adjacency and in-degree
        const inDegree = {};
        const children = {};
        for (const n of nodes) {
            inDegree[n.id] = 0;
            children[n.id] = [];
        }
        for (const e of edges) {
            inDegree[e.target] = (inDegree[e.target] || 0) + 1;
            if (children[e.source]) {
                children[e.source].push(e.target);
            }
        }

        // BFS for layers
        const queue = nodes
            .filter((n) => inDegree[n.id] === 0)
            .map((n) => n.id);
        const layers = {};
        let maxLayer = 0;

        for (const id of queue) {
            layers[id] = 0;
        }

        let qi = 0;
        while (qi < queue.length) {
            const current = queue[qi++];
            for (const child of children[current] || []) {
                const newLayer = layers[current] + 1;
                if (layers[child] === undefined || newLayer > layers[child]) {
                    layers[child] = newLayer;
                }
                inDegree[child]--;
                if (inDegree[child] === 0) {
                    queue.push(child);
                    maxLayer = Math.max(maxLayer, layers[child]);
                }
            }
        }

        // Position nodes by layer
        const layerNodes = {};
        for (const n of nodes) {
            const layer = layers[n.id] || 0;
            if (!layerNodes[layer]) layerNodes[layer] = [];
            layerNodes[layer].push(n);
        }

        const canvas = this.canvasRef.el;
        const canvasW = canvas ? canvas.width : 800;
        const canvasH = canvas ? canvas.height : 500;
        const layerCount = maxLayer + 1;
        const layerSpacing = canvasH / (layerCount + 1);

        for (let layer = 0; layer <= maxLayer; layer++) {
            const nodesInLayer = layerNodes[layer] || [];
            const colSpacing = canvasW / (nodesInLayer.length + 1);
            nodesInLayer.forEach((n, i) => {
                n.x = colSpacing * (i + 1);
                n.y = layerSpacing * (layer + 1);
            });
        }
    }

    _startAnimation() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;

        // Set canvas size
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = rect.width + "px";
        canvas.style.height = rect.height + "px";
        ctx.scale(dpr, dpr);

        const draw = () => {
            this._applyForces();
            this._render(ctx, rect.width, rect.height);
            this.animFrame = requestAnimationFrame(draw);
        };
        draw();
    }

    _applyForces() {
        const nodes = this.simNodes;
        const edges = this.simEdges;
        if (!nodes.length) return;

        const nodeMap = {};
        for (const n of nodes) nodeMap[n.id] = n;

        // Repulsion between all nodes
        const repulsion = 5000;
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i];
                const b = nodes[j];
                let dx = a.x - b.x;
                let dy = a.y - b.y;
                let dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = repulsion / (dist * dist);
                const fx = (dx / dist) * force;
                const fy = (dy / dist) * force;
                if (!a.fx) a.vx += fx;
                if (!a.fy) a.vy += fy;
                if (!b.fx) b.vx -= fx;
                if (!b.fy) b.vy -= fy;
            }
        }

        // Attraction along edges
        const attraction = 0.01;
        const idealLen = 120;
        for (const e of edges) {
            const a = nodeMap[e.source];
            const b = nodeMap[e.target];
            if (!a || !b) continue;
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (dist - idealLen) * attraction;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            if (!a.fx) a.vx += fx;
            if (!a.fy) a.vy += fy;
            if (!b.fx) b.vx -= fx;
            if (!b.fy) b.vy -= fy;
        }

        // Damping and position update
        const damping = 0.85;
        for (const n of nodes) {
            if (n.fx !== null) {
                n.x = n.fx;
                n.vx = 0;
            }
            if (n.fy !== null) {
                n.y = n.fy;
                n.vy = 0;
            }
            n.vx *= damping;
            n.vy *= damping;
            n.x += n.vx;
            n.y += n.vy;
        }
    }

    _render(ctx, w, h) {
        const nodes = this.simNodes;
        const edges = this.simEdges;
        const nodeMap = {};
        for (const n of nodes) nodeMap[n.id] = n;

        ctx.clearRect(0, 0, w, h);
        ctx.save();
        ctx.translate(this.pan.x, this.pan.y);
        ctx.scale(this.scale, this.scale);
        const isDark = cookie.get("color_scheme") === "dark";
        const edgeColor = isDark ? "#64748b" : "#94a3b8";

        // Draw edges (arrows)
        ctx.strokeStyle = edgeColor;
        ctx.lineWidth = 2;
        for (const e of edges) {
            const src = nodeMap[e.source];
            const tgt = nodeMap[e.target];
            if (!src || !tgt) continue;

            ctx.beginPath();
            ctx.moveTo(src.x, src.y);
            ctx.lineTo(tgt.x, tgt.y);
            ctx.stroke();

            // Arrowhead
            const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
            const r = 30; // node radius
            const ax = tgt.x - Math.cos(angle) * r;
            const ay = tgt.y - Math.sin(angle) * r;
            const headLen = 12;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(
                ax - headLen * Math.cos(angle - Math.PI / 6),
                ay - headLen * Math.sin(angle - Math.PI / 6)
            );
            ctx.lineTo(
                ax - headLen * Math.cos(angle + Math.PI / 6),
                ay - headLen * Math.sin(angle + Math.PI / 6)
            );
            ctx.closePath();
            ctx.fillStyle = edgeColor;
            ctx.fill();
        }

        // Draw nodes
        const nodeRadius = 28;
        const stateColors = {
            locked: isDark 
                ? { fill: "#475569", stroke: "#334155", text: "#e2e8f0" }
                : { fill: "#94a3b8", stroke: "#64748b", text: "#fff" },
            unlocked: isDark
                ? { fill: "#2563eb", stroke: "#1d4ed8", text: "#fff" }
                : { fill: "#3b82f6", stroke: "#1d4ed8", text: "#fff" },
            mastered: isDark
                ? { fill: "#16a34a", stroke: "#15803d", text: "#fff" }
                : { fill: "#22c55e", stroke: "#15803d", text: "#fff" },
        };

        for (const n of nodes) {
            const colors = stateColors[n.state] || stateColors.locked;

            // Shadow
            ctx.shadowColor = isDark ? "rgba(0,0,0,0.5)" : "rgba(0,0,0,0.15)";
            ctx.shadowBlur = 8;
            ctx.shadowOffsetX = 2;
            ctx.shadowOffsetY = 2;

            // Circle
            ctx.beginPath();
            ctx.arc(n.x, n.y, nodeRadius, 0, Math.PI * 2);
            ctx.fillStyle = colors.fill;
            ctx.fill();
            ctx.strokeStyle = colors.stroke;
            ctx.lineWidth = 2.5;
            ctx.stroke();

            // Reset shadow
            ctx.shadowColor = "transparent";
            ctx.shadowBlur = 0;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 0;

            // Label
            ctx.fillStyle = colors.text;
            ctx.font = "bold 11px Inter, system-ui, sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Truncate name if too long
            let label = n.name;
            if (label.length > 12) {
                label = label.substring(0, 10) + "…";
            }
            ctx.fillText(label, n.x, n.y);
        }

        ctx.restore();
    }

    _attachEvents() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;

        canvas.addEventListener("mousedown", (e) => this._onMouseDown(e));
        canvas.addEventListener("mousemove", (e) => this._onMouseMove(e));
        canvas.addEventListener("mouseup", (e) => this._onMouseUp(e));
        canvas.addEventListener("dblclick", (e) => this._onDblClick(e));
        canvas.addEventListener("wheel", (e) => this._onWheel(e));
    }

    _getCanvasCoords(e) {
        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        return {
            x: ((e.clientX - rect.left) - this.pan.x) / this.scale,
            y: ((e.clientY - rect.top) - this.pan.y) / this.scale,
        };
    }

    _findNodeAt(x, y) {
        const r = 28;
        for (const n of this.simNodes) {
            const dx = n.x - x;
            const dy = n.y - y;
            if (dx * dx + dy * dy <= r * r) {
                return n;
            }
        }
        return null;
    }

    _onMouseDown(e) {
        const coords = this._getCanvasCoords(e);
        const node = this._findNodeAt(coords.x, coords.y);
        if (node) {
            this.dragging = node;
            node.fx = node.x;
            node.fy = node.y;
            this.offset = { x: coords.x - node.x, y: coords.y - node.y };
        } else {
            this.isPanning = true;
            this.lastMouse = { x: e.clientX, y: e.clientY };
        }
    }

    _onMouseMove(e) {
        if (this.dragging) {
            const coords = this._getCanvasCoords(e);
            this.dragging.fx = coords.x - this.offset.x;
            this.dragging.fy = coords.y - this.offset.y;
            this.dragging.x = this.dragging.fx;
            this.dragging.y = this.dragging.fy;
        } else if (this.isPanning) {
            const dx = e.clientX - this.lastMouse.x;
            const dy = e.clientY - this.lastMouse.y;
            this.pan.x += dx;
            this.pan.y += dy;
            this.lastMouse = { x: e.clientX, y: e.clientY };
        }
    }

    _onMouseUp() {
        if (this.dragging) {
            this.dragging.fx = null;
            this.dragging.fy = null;
            this.dragging = null;
        }
        this.isPanning = false;
    }

    _onDblClick(e) {
        const coords = this._getCanvasCoords(e);
        const node = this._findNodeAt(coords.x, coords.y);
        if (node) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: "kms.node",
                res_id: node.id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    _onWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.scale = Math.max(0.3, Math.min(3, this.scale * delta));
    }
}

// Register as a client action so it can be opened from a menu item
registry.category("actions").add("kms_mastery.dag_viewer", DagViewer);
