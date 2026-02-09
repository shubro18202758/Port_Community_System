# SmartBerth AI Knowledge Base Summary

**Last Updated**: February 2025
**Total Documents**: 55 (6 original + 49 Azure DevOps)
**Total Chunks**: 477
**Vector Store**: ChromaDB (chroma_db_new)

---

## Knowledge Sources

### 1. Original Knowledge Base (6 documents)
Located in: `ai-service/knowledge_base/`
- SmartBerth_Constraint_Framework.md (39,989 chars) - 84 constraints, 6 layers
- SmartBerth_Domain_Knowledge.md (12,725 chars) - Port infrastructure
- Berth_Allocation_Knowledge.md (11,131 chars) - Scoring algorithms
- ETA_Prediction_Knowledge.md (9,465 chars) - Prediction methodology
- Constraint_Rules.md (8,175 chars) - Validation logic

### 2. Azure DevOps Knowledge Docs (49 documents)
Located in: `ai-backend/knowledge_docs/`

#### Port Manuals (10 documents)
- Physical dimensions, cargo compatibility, berth equipment
- Resource availability, tidal/weather constraints
- Priority/commercial rules, window vessel operations
- UKC navigation safety, maintenance, decision framework

#### Historical Logs (18 documents)
- Berth allocation patterns 2024
- Resource utilization patterns
- Dwell time analysis, waiting time patterns
- 8 optimization run case studies

#### Weather Studies (10 documents)
- Storm impact analysis (18 events)
- Tidal window analysis, fog visibility
- 6 weather factor studies

#### Best Practices (10 documents)
- PortCDM international standards
- Optimization techniques (BAP, OR-Tools)
- Safety management, resource allocation
- 5 industry benchmark studies

---

## RAG Integration Status

✅ ChromaDB collection: `smartberth_knowledge`
✅ Embedding model: `all-MiniLM-L6-v2`
✅ Claude Opus 4 API integration ready
✅ Category-aware retrieval enabled

## Quick Reference

- **Port**: JNPT (18.9453°N, 72.9400°E)
- **Berths**: 18 total
- **Max Draft**: 16.0m (BMCT)
- **Max LOA**: 340m (GTI)
- **Hard Constraints**: 12 (never violate)
- **Soft Constraints**: 6 (optimization weights)
- **UKC Formula**: Static Draft + Squat + Heel + Wave + Safety Margin
