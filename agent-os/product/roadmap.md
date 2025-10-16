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
- [x] Docker Compose setup with PostgreSQL and Python containers (SPEC-004)
- [x] Database migrations and initialization scripts
- [x] Integration testing suite (16 tests passing)
- [x] GitHub repository created and pushed

### Deliverables
- Working API client with rate limit handling
- PostgreSQL database schema ready for deployment
- Development standards in `agent-os/standards/`
- Complete product documentation in `agent-os/product/`
- Production-ready Docker infrastructure
- Comprehensive documentation (development.md, deployment.md, troubleshooting.md)

---

## Phase 1: MVP - Character Analysis

**Timeline**: Week 2-4 (Oct 16 - Nov 5, 2025)
**Status**: 📋 Ready to Start
**Priority**: P0 (Critical)
**Specification**: **SPEC-005** (consolidates SPEC-001, SPEC-002, SPEC-003)

### Goals
Prove the concept by implementing an end-to-end data pipeline: discover players → collect matches → analyze character win rates → identify teammate synergies.

### Features

#### 1.1 End-to-End Data Pipeline
**SPEC**: SPEC-005 Character Analysis MVP
**Dependencies**: SPEC-004 (Docker, database, API client) - ✅ Complete
**Tasks**: 53 subtasks across 8 task groups (40-54 hours)
**Documentation**: `/home/ericreyes/github/marvel-rivals-stats/agent-os/specs/20251015-character-analysis-mvp/`

**Implementation Phases**:

1. **Player Discovery** (Task Group 2: 6-8 hours)
   - Stratified sampling across 8 rank tiers (500 players total)
   - Leaderboard API integration with rate limiting
   - Player deduplication and database insertion
   - Progress tracking and resumable collection
   - CLI script: `scripts/discover_players.py`

2. **Match Collection** (Task Group 3: 8-10 hours)
   - Fetch 100-150 matches per player (50,000+ total matches)
   - Match deduplication by match_id
   - Extract 12 participants per match with performance stats
   - Rate limiter integration (7 req/min, 8.6s delays)
   - Resumable collection with progress reporting
   - CLI script: `scripts/collect_matches.py`

3. **Character Win Rate Analysis** (Task Group 4: 6-8 hours)
   - Calculate win rates for all 40+ heroes
   - Rank stratification (Bronze → Celestial)
   - Wilson confidence intervals (95% confidence)
   - Minimum sample filtering (30 games per rank, 100 overall)
   - Database caching in character_stats table
   - JSON export with confidence intervals
   - CLI script: `scripts/analyze_character.py`

4. **Teammate Synergy Analysis** (Task Group 5: 8-10 hours) **[NEW]**
   - Calculate actual vs expected win rates for hero pairs
   - Synergy score: `actual_win_rate - expected_win_rate`
   - Identify top 10 teammates for each hero
   - Minimum 50 games together threshold
   - Database caching in synergy_stats table
   - JSON export with synergy rankings
   - CLI script: `scripts/analyze_synergy.py`

**Acceptance Criteria**:
- ✅ 400+ players discovered (80% of target, stratified by rank)
- ✅ 50,000+ unique matches collected and deduplicated
- ✅ API rate limits respected (no 429 errors)
- ✅ 35+ heroes analyzed with win rates per rank tier
- ✅ Top 10 synergies identified for 30+ heroes
- ✅ All results include 95% confidence intervals
- ✅ Pipeline is resumable (no data loss on interruption)
- ✅ 20-28 tests passing (unit + integration)
- ✅ Results exported to JSON format

### Deliverables
- **4 working CLI scripts** (discover, collect, analyze character, analyze synergy)
- **JSON exports** with character win rates and synergy data
- **Cached results** in database (character_stats, synergy_stats tables)
- **Test suite** (20-28 tests covering critical paths)
- **Updated documentation** with usage examples and statistical methodology
- **Verification report** confirming all acceptance criteria met

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
- [x] CI/CD pipeline (GitHub Actions)

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

## Phase 3: Web Frontend & Enhanced Visualizations

**Timeline**: Week 6-8 (Nov 16 - Dec 7, 2025)
**Status**: 📋 Planned
**Priority**: P1 (High)

### Goals
Build user-facing web interface to visualize character statistics and synergy data from Phase 1.

### Features

#### 3.1 Next.js Web Frontend
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Set up Tailwind CSS for styling
- [ ] Build hero stats pages with Recharts visualizations
- [ ] Create homepage with top heroes by rank
- [ ] Add hero comparison tool
- [ ] Deploy frontend container to Odin
- [ ] Integrate with Caddy reverse proxy

#### 3.2 Synergy Visualizations
**Data Source**: Phase 1 synergy_stats table (from SPEC-005)

- [ ] Build interactive synergy matrix UI
- [ ] Display top synergies per hero with confidence intervals
- [ ] Add filtering by rank tier
- [ ] Create synergy heatmap visualization
- [ ] Add API endpoints to FastAPI backend for synergy data

#### 3.3 Enhanced Statistics Pages
- [ ] Win rate trend charts (by rank)
- [ ] Confidence interval visualizations
- [ ] Role-based filtering and comparisons
- [ ] Sample size indicators
- [ ] Statistical significance badges

#### 3.4 Role-based Insights
- [ ] Best Vanguards for each Strategist
- [ ] Best Duelists for each Vanguard
- [ ] Optimal role distribution insights (if data supports)
- [ ] Cross-role synergy recommendations

### Deliverables
- **Public web interface at rivals.jinocenc.io**
- Interactive hero statistics pages
- Synergy matrix and top recommendations UI
- API endpoints serving Phase 1 cached data
- Responsive design for mobile/desktop
- Documentation for web interface usage

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

### Phase 1 (MVP - SPEC-005)
- ✅ Collect 50,000+ matches from 400+ players (stratified by rank)
- ✅ Calculate win rates for 35+ heroes with confidence intervals
- ✅ Identify top 10 synergies per hero (NEW)
- ✅ Export JSON with statistical rigor (confidence intervals, sample sizes)
- ✅ Pipeline is resumable and respects API rate limits
- ✅ 20-28 tests passing (minimal testing philosophy)
- ✅ Results correlate with community tier lists (±5%)

### Phase 2 (Polish + Web API)
- ✅ Enhanced test coverage (strategic integration tests)
- ✅ All heroes with 100+ games analyzed
- ✅ Multiple export formats available
- ✅ CI/CD pipeline passing
- ✅ **Web API deployed to rivals.jinocenc.io**
- ✅ PostgreSQL database operational on Odin

### Phase 3 (Frontend + Visualizations)
- ✅ **Public web interface accessible at rivals.jinocenc.io**
- ✅ Hero pages with interactive charts and confidence intervals
- ✅ Synergy matrix visualization (using Phase 1 data)
- ✅ Role-based filtering and comparisons
- ✅ Mobile-responsive design

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
