# Marvel Rivals Stats Analyzer - Roadmap

## Overview

This roadmap outlines the phased development plan for the Marvel Rivals Stats Analyzer, organized by feature priority and dependencies.

---

## Phase 0: Foundation (COMPLETED)

**Timeline**: Week 1 (Oct 8-15, 2025)
**Status**: ✅ Complete

### Goals
Establish project structure, database schema, and API integration foundation.

### Completed Features
- [x] Project scaffolding and directory structure
- [x] Database schema design (PostgreSQL)
- [x] Marvel Rivals API client with rate limiting
- [x] Environment configuration (.env setup)
- [x] Initial test scripts (test_api.py, init_db.py)
- [x] Sample data seeding capability
- [x] Documentation (README, PLAN.md, PRODUCT.md)
- [x] Specification documents (SPEC-001, SPEC-002, SPEC-003)
- [x] Product planning (mission.md, roadmap.md, tech-stack.md)

### Deliverables
- Working API client with rate limit handling
- PostgreSQL database schema ready for deployment
- Development standards in `agent-os/standards/`
- Complete product documentation in `agent-os/product/`

---

## Phase 1: MVP - Character Analysis

**Timeline**: Week 2-3 (Oct 16-30, 2025)
**Status**: 🚧 In Progress
**Priority**: P0 (Critical)

### Goals
Prove the concept by collecting data for 500 players and analyzing character win rates.

### Features

#### 1.1 Player Discovery
**SPEC**: SPEC-001
**Dependencies**: API client, database schema

- [ ] Implement player discovery module (`src/collectors/player_discovery.py`)
- [ ] Create discovery CLI script (`scripts/discover_players.py`)
- [ ] Support stratified sampling by rank tier
- [ ] Implement quota-based collection
- [ ] Add progress tracking and resume capability

**Acceptance Criteria**:
- Discover 500+ players across all rank tiers
- At least 5 players per rank tier
- No duplicates in database
- Process respects API rate limits

#### 1.2 Match History Collection
**SPEC**: SPEC-002
**Dependencies**: Player discovery completed

- [ ] Implement match collector module (`src/collectors/match_collector.py`)
- [ ] Create collection CLI script (`scripts/collect_matches.py`)
- [ ] Handle match deduplication
- [ ] Extract participant data (hero, role, stats, outcome)
- [ ] Implement rate limiting and error handling
- [ ] Add batch processing with resume capability

**Acceptance Criteria**:
- Collect 50,000+ unique matches
- 80%+ of discovered players have matches collected
- All matches have 12 participants (6v6)
- Deduplication works correctly

#### 1.3 Character Win Rate Analysis
**SPEC**: SPEC-003
**Dependencies**: Match collection completed

- [ ] Implement character analysis module (`src/analyzers/character_winrate.py`)
- [ ] Add Wilson confidence interval calculation
- [ ] Create analysis CLI script (`scripts/analyze_character.py`)
- [ ] Implement rank stratification
- [ ] Add minimum sample size filtering (30 games)
- [ ] Export results to JSON

**Acceptance Criteria**:
- All heroes with 100+ games analyzed
- Win rates calculated for all rank tiers with 30+ games
- 95% confidence intervals included
- Results exported to JSON format

### Deliverables
- 3 working CLI scripts (discover, collect, analyze)
- JSON exports with character win rates
- Cached results in database
- Updated documentation with usage examples

---

## Phase 2: Full Coverage & Polish

**Timeline**: Week 4-5 (Oct 31 - Nov 15, 2025)
**Status**: 📋 Planned
**Priority**: P1 (High)

### Goals
Expand sample size, improve data quality, and add testing infrastructure.

### Features

#### 2.1 Expanded Data Collection
- [ ] Increase sample to 1000+ players
- [ ] Implement snowball sampling (discover players from matches)
- [ ] Add data quality checks and validation
- [ ] Implement periodic refresh mechanism

#### 2.2 Testing & Quality
- [ ] Add unit tests for all modules (pytest)
- [ ] Integration tests with sample data
- [ ] Type checking with mypy
- [ ] Code formatting with black
- [ ] Linting with ruff
- [ ] CI/CD pipeline (GitHub Actions)

#### 2.3 Enhanced Statistics
- [ ] Add percentile rankings (hero vs. hero comparisons)
- [ ] Calculate performance metrics (K/D, damage, healing)
- [ ] Add role-specific analysis
- [ ] Implement statistical significance testing

#### 2.4 Improved Exports
- [ ] CSV export option
- [ ] Enhanced JSON with metadata
- [ ] Summary reports (top 10 heroes per rank)
- [ ] Visualization-ready data formats

#### 2.5 Web Application Foundation
- [ ] Set up PostgreSQL database on Odin
- [ ] Create Docker Compose configuration
- [ ] Build FastAPI backend with basic endpoints
- [ ] Deploy to Odin with Caddy reverse proxy
- [ ] Configure subdomain: `rivals.jinocenc.io`

### Deliverables
- Comprehensive test suite with 80%+ coverage
- Enhanced analysis with performance metrics
- Multiple export formats
- CI/CD pipeline
- **Web API accessible at rivals.jinocenc.io**

---

## Phase 3: Web Frontend & Synergy Analysis

**Timeline**: Week 6-8 (Nov 16 - Dec 7, 2025)
**Status**: 📋 Planned
**Priority**: P1 (High)

### Goals
Build user-facing web interface and analyze team compositions to identify hero synergies.

### Features

#### 3.1 Next.js Web Frontend
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Set up Tailwind CSS for styling
- [ ] Build hero stats pages with Recharts visualizations
- [ ] Create homepage with top heroes by rank
- [ ] Add hero comparison tool
- [ ] Deploy frontend container to Odin
- [ ] Integrate with Caddy reverse proxy

#### 3.2 Pair-wise Synergy Analysis
**SPEC**: TBD (SPEC-004)

- [ ] Create synergy analyzer module (`src/analyzers/team_synergy.py`)
- [ ] Calculate expected vs. actual win rates for hero pairs
- [ ] Implement synergy score calculation
- [ ] Add statistical significance testing
- [ ] Filter for minimum sample size (50 games together)
- [ ] Add synergy API endpoints to FastAPI backend

#### 3.3 Role-based Analysis
- [ ] Best tanks for each support
- [ ] Best DPS for each tank
- [ ] Optimal role distribution analysis (2-2-2 vs alternatives)
- [ ] Visualize synergies in web UI

#### 3.4 Synergy CLI & Export
- [ ] Create synergy analysis script (`scripts/analyze_synergy.py`)
- [ ] Export synergy matrix to JSON
- [ ] Generate top synergy recommendations per hero
- [ ] Cache results in database

### Deliverables
- **Public web interface at rivals.jinocenc.io**
- Synergy analysis module
- CLI script for synergy analysis
- JSON exports with synergy data
- Interactive synergy visualizations
- Documentation for synergy methodology

---

## Phase 4: Advanced Features

**Timeline**: Week 9-12 (Dec 8 - Jan 4, 2026)
**Status**: 💡 Backlog
**Priority**: P2 (Medium)

### Goals
Add advanced analytics and time-series tracking.

### Features

#### 4.1 Full Team Composition Analysis
- [ ] Analyze 6-hero team templates
- [ ] Identify winning composition patterns
- [ ] Compare 2-2-2 vs 1-3-2 vs 3-1-2 effectiveness

#### 4.2 Counter-pick Analysis
- [ ] Calculate hero matchup win rates
- [ ] Identify counter-picks (hero A vs. hero B)
- [ ] Generate counter-pick recommendations

#### 4.3 Meta Tracking Over Time
- [ ] Track win rate changes across patches
- [ ] Identify emerging and declining heroes
- [ ] Visualize meta evolution
- [ ] Detect meta shifts automatically

#### 4.4 Performance Optimization
- [ ] Database indexing optimization
- [ ] Query performance improvements
- [ ] Parallel processing for analysis
- [ ] Redis caching layer for API responses
- [ ] Result caching strategies

#### 4.5 Infrastructure Improvements
- [ ] Set up automated data collection (cron/systemd timers)
- [ ] Database backup automation (to NFS mount)
- [ ] Monitoring with Prometheus + Grafana
- [ ] Error tracking and logging improvements
- [ ] Health check endpoints

### Deliverables
- Advanced composition analysis
- Counter-pick recommendations
- Time-series meta tracking
- Performance-optimized codebase
- **Production-grade infrastructure with monitoring**

---

## Phase 5: Community & Integration

**Timeline**: Q2 2026
**Status**: 💡 Backlog
**Priority**: P3 (Low)

### Goals
Enable community contributions and third-party integrations.

### Features

#### 5.1 Public API & Documentation
- [ ] OpenAPI/Swagger documentation (auto-generated by FastAPI)
- [ ] API rate limiting for public endpoints
- [ ] Optional Discord OAuth authentication for advanced features
- [ ] Example integrations (Discord bot, tier list tool)
- [ ] API usage analytics

#### 5.2 Enhanced Web Features
- [ ] User accounts (optional, via Discord OAuth)
- [ ] Favorite heroes tracking
- [ ] Custom tier list builder
- [ ] Embeddable widgets for content creators
- [ ] SEO optimization for hero pages

#### 5.3 Community Features
- [ ] Contribution guidelines
- [ ] Community feedback form
- [ ] Discord bot for stat lookups
- [ ] Data export API for researchers
- [ ] Public dataset releases (periodic)

#### 5.4 Scale-Out Planning
- [ ] Document migration path to hosted PostgreSQL (e.g., Neon, Supabase)
- [ ] CDN integration for static assets (Cloudflare)
- [ ] Horizontal scaling strategy if traffic grows
- [ ] Cost analysis for hosted services

### Deliverables
- **Public REST API with documentation**
- Discord bot integration
- Enhanced web features with auth
- Community contribution framework
- **Migration plan for scaling beyond Odin**

---

## Dependencies & Blockers

### External Dependencies
- **Marvel Rivals API**: Must remain stable and accessible
- **API Rate Limits**: 10,000 requests/day (free tier)
- **Game Patches**: May invalidate data, require re-collection
- **Odin Server**: Must remain operational for hosting
- **Caddy Reverse Proxy**: Integration with existing server-stack

### Technical Dependencies
```
Phase 1 (MVP - CLI)
└── Phase 2 (Polish + Web API) [requires Phase 1 data + PostgreSQL setup]
    └── Phase 3 (Frontend + Synergies) [requires Phase 2 API + Docker deployment]
        └── Phase 4 (Advanced + Infrastructure) [requires Phase 3 web presence]
            └── Phase 5 (Community + Scale-out) [requires Phase 4 stability]
```

### Infrastructure Dependencies
- **Phase 1**: Local development only
- **Phase 2**: PostgreSQL on Odin, Docker setup, Caddy configuration
- **Phase 3**: Next.js deployment, multi-container orchestration
- **Phase 4**: Redis, monitoring stack (Prometheus/Grafana)
- **Phase 5**: Consider hosted services if traffic exceeds server capacity

---

## Risk Management

### High-Priority Risks

**Risk**: API rate limits prevent data collection
**Mitigation**: Implement aggressive caching, request throttling, batch processing

**Risk**: Insufficient sample sizes for rare heroes
**Mitigation**: Document sample sizes, filter results, consider longer collection period

**Risk**: Player rank data is stale or missing
**Mitigation**: Validate rank data quality, document limitations, filter WHERE NOT NULL

**Risk**: Odin server outage or resource constraints
**Mitigation**: Monitor resource usage, database backups to NFS, document migration path to hosted services

### Medium-Priority Risks

**Risk**: Statistical calculations are incorrect
**Mitigation**: Use well-tested scipy library, add comprehensive unit tests, peer review

**Risk**: Community misinterprets results
**Mitigation**: Include confidence intervals, document methodology, add disclaimers

**Risk**: Web traffic exceeds server capacity
**Mitigation**: Implement caching (Redis), CDN for static assets, consider migration to hosted services if needed

---

## Success Criteria by Phase

### Phase 1 (MVP)
- ✅ Collect 50,000+ matches from 500+ players
- ✅ Calculate win rates for 30+ heroes
- ✅ Export JSON with confidence intervals
- ✅ Results correlate with community tier lists (±5%)

### Phase 2 (Polish + Web API)
- ✅ 80%+ test coverage
- ✅ All heroes with 100+ games analyzed
- ✅ Multiple export formats available
- ✅ CI/CD pipeline passing
- ✅ **Web API deployed to rivals.jinocenc.io**
- ✅ PostgreSQL database operational on Odin

### Phase 3 (Frontend + Synergies)
- ✅ Identify top 10 synergies per hero
- ✅ Statistical significance p < 0.05
- ✅ Results reveal insights not in community knowledge
- ✅ **Public web interface accessible**
- ✅ Hero pages with interactive charts

### Phase 4 (Advanced + Infrastructure)
- ✅ Track meta across 3+ patches
- ✅ Counter-pick recommendations validated
- ✅ Full composition templates generated
- ✅ **Automated data collection running**
- ✅ Monitoring and backups configured

### Phase 5 (Community + Scale)
- ✅ 10+ content creators use data
- ✅ API serves 100+ requests/day
- ✅ Community contributions accepted
- ✅ **Migration path documented for hosted services**
- ✅ Discord bot integration operational

---

## Timeline Summary

| Phase | Duration | Target Completion | Status |
|-------|----------|-------------------|--------|
| Phase 0: Foundation | 1 week | Oct 15, 2025 | ✅ Complete |
| Phase 1: MVP | 2-3 weeks | Oct 30, 2025 | 🚧 In Progress |
| Phase 2: Polish | 2 weeks | Nov 15, 2025 | 📋 Planned |
| Phase 3: Synergies | 3 weeks | Dec 7, 2025 | 📋 Planned |
| Phase 4: Advanced | 4 weeks | Jan 4, 2026 | 💡 Backlog |
| Phase 5: Community | 8+ weeks | Q2 2026 | 💡 Backlog |

**Total MVP to Production**: ~10 weeks (Oct 15 - Dec 31, 2025)

---

**Last Updated**: 2025-10-15
