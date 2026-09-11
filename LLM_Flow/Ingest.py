from Core.Documents import KnowledgeBase

knowledge = KnowledgeBase()

results = knowledge.ingest_folder()

for result in results:
    print(result)
