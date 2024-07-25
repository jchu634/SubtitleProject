## Ryzen Subtitles Frontend
This is a [Next.js](https://nextjs.org/) pages-router frontend bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

UI components are built using [ShadCN UI](https://ui.shadcn.com),  [Tailwind CSS](https://tailwindcss.com/) and [Luicide Icons](https://lucide.dev/).

There are some custom bindings for a Python-JS api which links with [PyWebView](https://pywebview.flowrl.com/guide/usage.html#communication-between-javascript-and-python) for Window management purposes.\
Otherwise the communication is done through a fairly standard web API.

## Getting Started
First, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.