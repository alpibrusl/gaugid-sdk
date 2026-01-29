# Protocol Extension Proposal Summary

## Memory Types Extension for a2p Protocol v0.1.0 (Initial Release)

**Quick Summary**: This proposal adds **semantic** and **procedural** memory types to the a2p protocol specification, alongside the existing episodic memory.

### Why This Matters

Modern agent frameworks (LangGraph, Google ADK) organize memory into three types:
- **Episodic**: Specific events ("what happened when")
- **Semantic**: General knowledge ("what the user knows")  
- **Procedural**: Behavioral patterns ("how the user does things")

Currently, a2p only supports episodic memory. Adding semantic and procedural types will:
- ✅ Align with industry-standard memory architectures
- ✅ Enable better context retrieval via semantic search
- ✅ Support richer personalization through behavioral patterns
- ✅ Maintain full backward compatibility

### Proposed Changes

**Protocol Spec** (`docs/spec/README.md` Section 6):
```json
{
  "memories": {
    "a2p:episodic": [...],      // Existing
    "a2p:semantic": [...],       // NEW
    "a2p:procedural": [...]      // NEW
  }
}
```

**Type Definitions** (`packages/sdk-python/src/a2p/types.py`):
- Extend `Memories` model with `semantic` and `procedural` fields
- Both fields are optional (backward compatible)

### Key Benefits

1. **Interoperability**: All implementations use the same memory model
2. **Framework Alignment**: Matches LangGraph and ADK patterns
3. **Better Search**: Semantic search finds relevant memories across types
4. **Richer Context**: Procedural memory captures behavioral patterns

### Backward Compatibility

- ✅ Existing profiles remain valid
- ✅ Existing SDKs continue to work (new fields optional)
- ✅ Default behavior unchanged (episodic if type not specified)

### Timeline

- **Specification**: 2 weeks
- **Implementation**: 2 weeks  
- **Documentation**: 1 week
- **Release**: Included in v0.1.0 initial community release

### Full Proposal

See [memory-types-protocol-extension.md](./memory-types-protocol-extension.md) for complete details.

### Next Steps

1. Review proposal with a2p protocol team
2. Gather community feedback
3. Approve or request revisions
4. Begin implementation if approved

---

**Questions?** Contact the Gaugid SDK team or open a discussion in the a2p protocol repository.
