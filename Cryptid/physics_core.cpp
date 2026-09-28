#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include <vector>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

struct Node {
    float mass = 1.0f;
    float x = 0.0f;
    float y = 0.0f;
    float vx = 0.0f;
    float vy = 0.0f;
    float ax = 0.0f;
    float ay = 0.0f;
};

struct Beam {
    int node_a;
    int node_b;
    float rest_length;
    float stiffness;
    float damping;
    float plastic_yield_threshold;
    float plastic_creep_rate;
};

PYBIND11_MAKE_OPAQUE(std::vector<Node>);
PYBIND11_MAKE_OPAQUE(std::vector<Beam>);

class PhysicsWorld {
public:
    std::vector<Node> nodes;
    std::vector<Beam> beams;

    int add_node(float mass, float x, float y) {
        nodes.push_back({mass, x, y, 0.0f, 0.0f, 0.0f, 0.0f});
        return static_cast<int>(nodes.size() - 1);
    }

    int add_beam(int a, int b, float rest_len, float k, float c, float yield_thresh, float creep) {
        beams.push_back({a, b, rest_len, k, c, yield_thresh, creep});
        return static_cast<int>(beams.size() - 1);
    }

    void step(float dt, float bounds_width, float bounds_height) {
        if (dt <= 0.0f) return;

        const int SUBSTEPS = 8;
        float sub_dt = dt / static_cast<float>(SUBSTEPS);
        float restitution = 0.3f;
        float friction = 0.95f;

        for (int sub = 0; sub < SUBSTEPS; ++sub) {
            // --- A. VELOCITY VERLET STEP 1 ---
            for (auto& n : nodes) {
                if (n.mass <= 0.0f) continue;
                n.x += n.vx * sub_dt + 0.5f * n.ax * sub_dt * sub_dt;
                n.y += n.vy * sub_dt + 0.5f * n.ay * sub_dt * sub_dt;
                n.vx += 0.5f * n.ax * sub_dt;
                n.vy += 0.5f * n.ay * sub_dt;
                n.ax = 0.0f;
                n.ay = 0.0f;
            }

            // --- B. FORCE ACCUMULATION ---
            for (auto& b : beams) {
                Node& na = nodes[b.node_a];
                Node& nb = nodes[b.node_b];

                float dx = nb.x - na.x;
                float dy = nb.y - na.y;
                float dist = std::sqrt(dx * dx + dy * dy);

                if (dist < 1e-6f) continue;

                float nx = dx / dist;
                float ny = dy / dist;
                float v_diff = (nb.vx - na.vx) * nx + (nb.vy - na.vy) * ny;

                float spring_force = b.stiffness * (dist - b.rest_length);
                float damping_force = b.damping * v_diff;
                float total_force = spring_force + damping_force;

                // Plastic Deformation (Permanent bending)
                if (std::abs(total_force) > b.plastic_yield_threshold) {
                    float sign = (total_force > 0.0f) ? 1.0f : -1.0f;
                    b.rest_length += sign * b.plastic_creep_rate * sub_dt;
                    if (b.rest_length < 0.01f) b.rest_length = 0.01f;
                }

                float fx = total_force * nx;
                float fy = total_force * ny;

                if (na.mass > 0.0f) { na.ax += fx / na.mass; na.ay += fy / na.mass; }
                if (nb.mass > 0.0f) { nb.ax -= fx / nb.mass; nb.ay -= fy / nb.mass; }
            }

            // --- C. VELOCITY VERLET STEP 2 & BOUNDARY COLLISIONS ---
            for (auto& n : nodes) {
                if (n.mass > 0.0f) {
                    n.vx += 0.5f * n.ax * sub_dt;
                    n.vy += 0.5f * n.ay * sub_dt;

                    // Screen-edge boundary checks
                    if (n.x < 0.0f) {
                        n.x = 0.0f;
                        n.vx = -n.vx * restitution;
                        n.vy *= friction;
                    }
                    else if (n.x > bounds_width) {
                        n.x = bounds_width;
                        n.vx = -n.vx * restitution;
                        n.vy *= friction;
                    }

                    if (n.y < 0.0f) {
                        n.y = 0.0f;
                        n.vy = -n.vy * restitution;
                        n.vx *= friction;
                    }
                    else if (n.y > bounds_height) {
                        n.y = bounds_height;
                        n.vy = -n.vy * restitution;
                        n.vx *= friction;
                    }
                }
            }
        }
    }
};

PYBIND11_MODULE(physics_core, m) {
    m.doc() = "Optimized C++ 2D Soft-Body Physics Engine";

    py::bind_vector<std::vector<Node>>(m, "NodeVector");
    py::bind_vector<std::vector<Beam>>(m, "BeamVector");

    py::class_<Node>(m, "Node")
        .def(py::init<>())
        .def_readwrite("mass", &Node::mass)
        .def_readwrite("x", &Node::x)
        .def_readwrite("y", &Node::y)
        .def_readwrite("vx", &Node::vx)
        .def_readwrite("vy", &Node::vy)
        .def_readwrite("ax", &Node::ax)
        .def_readwrite("ay", &Node::ay);

    py::class_<Beam>(m, "Beam")
        .def(py::init<>())
        .def_readwrite("node_a", &Beam::node_a)
        .def_readwrite("node_b", &Beam::node_b)
        .def_readwrite("rest_length", &Beam::rest_length)
        .def_readwrite("stiffness", &Beam::stiffness)
        .def_readwrite("damping", &Beam::damping)
        .def_readwrite("plastic_yield_threshold", &Beam::plastic_yield_threshold)
        .def_readwrite("plastic_creep_rate", &Beam::plastic_creep_rate);

    py::class_<PhysicsWorld>(m, "PhysicsWorld")
        .def(py::init<>())
        .def_readwrite("nodes", &PhysicsWorld::nodes)
        .def_readwrite("beams", &PhysicsWorld::beams)
        .def("add_node", &PhysicsWorld::add_node)
        .def("add_beam", &PhysicsWorld::add_beam)
        .def("step", &PhysicsWorld::step, py::arg("dt"), py::arg("bounds_width"), py::arg("bounds_height"));
}