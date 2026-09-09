dualeapa-sprint1-project/
├── README.md (navigation hub)
├── .agent.md (AI guidance)
│
├── backend/              ← Spring Boot API + Database
│   ├── README.md         ← HOW TO RUN BACKEND (dev, docker, tests)
│   ├── .agent.md
│   ├── pom.xml
│   ├── src/
│   └── db/migrations/    ← Flyway: V001, V002, V003...
│
├── frontend/             ← Angular 22.1 App
│   ├── README.md         ← HOW TO RUN FRONTEND (dev, SSR, docker, tests)
│   ├── .agent.md
│   ├── package.json
│   └── libs/ui/          ← Component library
│
├── services/
│   └── auth/             ← Next.js Auth Service
│       ├── README.md     ← HOW TO RUN AUTH (dev, docker, tests)
│       ├── .agent.md
│       └── src/app/api/auth/ ← /login, /register, /refresh, /verify
│
├── scripts/              ← Python Analytics & Backtesting
│   ├── README.md         ← HOW TO RUN SCRIPTS (dev, docker, tests)
│   ├── .agent.md
│   ├── requirements.txt
│   ├── backtesting/      ← run_backtest.py + strategies
│   └── analytics/        ← report_generator.py
│
├── infrastructure/       ← DevOps & Deployment
│   ├── README.md         ← HOW TO DEPLOY (full stack, individual, prod)
│   ├── .agent.md
│   ├── docker/           ← Dockerfiles for all services
│   ├── docker-compose/   ← docker-compose.yml + prod config
│   └── jenkins/          ← Jenkinsfile + pipeline scripts
│
├── docs/                 ← Centralized Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DATABASE.md
│   ├── DEVELOPMENT_WORKFLOW.md
│   └── DEPLOYMENT.md
│
└── .github/workflows/    ← GitHub Actions (optional)