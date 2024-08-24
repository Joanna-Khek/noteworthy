```plantuml
group Apprentice retrieve feedback

actor Apprentice

Apprentice -> WebApp: get_llm_output(assignment, question)
database Folder
WebApp -> Folder: retrieve(assignment, question)
Folder -> WebApp: return_result()
WebApp -> Apprentice: display_review()

end

actor Operator
Operator -> Controller: trigger data pipeline

group Data Pipeline

Controller -[#red]> DataManager: trigger data manager pipeline

database GitLabRepo
DataManager -[#red]> GitLabRepo: extract_all_files
GitLabRepo -[#red]> DataManager: download [*.py & *.ipynb]
DataManager -[#red]> Folder: save [*.py & *.ipynb]

Controller -[#blue]> DataProcessor: trigger data processor pipeline
DataProcessor -[#blue]> Folder: save [input.csv]

Controller -[#green]> LLM: trigger llm pipeline
LLM -[#green]> AzureLLMService: run_invoke(question)
AzureLLMService -[#green]> LLM: return [llm_answers]
LLM -[#green]> Folder: save [output.csv]

end
```

```plantuml

database "Folder" {
  folder "raw" {
    [branches]
  }
  folder "processed" {
    [assignment]
  }
}

[GitLab]



node "DataPipeline"{

[DataManager] --> [branches]: writes
[DataManager] <-- GitLab: downloads
[DataProcessor] --> [assignment]: writes
[DataProcessor] <-- [branches]: reads
[LLM] --> [assignment]: writes
[LLM] <-- [assignment]: reads

[Controller]


}

[UI] --> [assignment]: reads

end
```
