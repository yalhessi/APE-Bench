Now, we would like to prove a variant of the upcrossing estimate obtained by taking the supremum
over $N$ of the original upcrossing estimate. Namely, we want the inequality
$$
  (b - a) \sup_N \mathbb{E}[U_N(a, b)] \le \sup_N \mathbb{E}[(f_N - a)^+].
$$
This inequality is central for the martingale convergence theorem as it provides a uniform bound
for the upcrossings.

We note that on top of taking the supremum on both sides of the inequality, we had also used
the monotone convergence theorem on the left-hand side to take the supremum outside of the
integral. To do this, we need to make sure $U_N(a, b)$ is measurable and integrable. Integrability
is easy to check as $U_N(a, b) ≤ N$ and so it suffices to show measurability. Indeed, by
noting that
$$
  U_N(a, b) = \sum_{i = 1}^N \mathbf{1}_{\{\tau_i < N\}}
$$
$U_N(a, b)$ is measurable as $\{\tau_i < N\}$ is a measurable set since $\tau_i$ is a
stopping time.
