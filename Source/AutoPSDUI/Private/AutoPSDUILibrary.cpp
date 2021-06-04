// Copyright 2018-2021 - John snow wind
#include "AutoPSDUILibrary.h"
#include "AutoPSDUISetting.h"

#include "IPythonScriptPlugin.h"
#include "AssetRegistry/AssetRegistryModule.h"

#include "WidgetBlueprint.h"
#include "WidgetBlueprintFactory.h"
#include "IAssetTools.h"
#include "AssetToolsModule.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "EditorAssetLibrary.h"

#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"

#include "Components/Widget.h"
#include "Components/CanvasPanel.h"

void UAutoPSDUILibrary::RunPyCmd(const FString& PyCmd)
{
	IPythonScriptPlugin::Get()->ExecPythonCommand(*PyCmd);
}

UObject* UAutoPSDUILibrary::ImportImage(const FString& SrcFile, const FString& AssetPath)
{
	return nullptr;
}

UWidgetBlueprint* UAutoPSDUILibrary::CreateWBP(const FString& AssetPath)
{
	UWidgetBlueprintFactory* Factory = NewObject<UWidgetBlueprintFactory>();
	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
	Factory->ParentClass = UUserWidget::StaticClass();

	const FString AssetName = FPaths::GetBaseFilename(AssetPath);
	const FString PackagePath = FPaths::GetPath(AssetPath);
	UWidgetBlueprint* Asset = Cast<UWidgetBlueprint>(AssetTools.CreateAsset(*AssetName, *PackagePath, nullptr, Factory));
	return Asset;
}


UWidget* UAutoPSDUILibrary::MakeWidgetWithWBP(UClass* WidgetClass, UWidgetBlueprint* ParentWBP, const FString& WidgetName)
{
	UWidgetTree* WidgetTree = ParentWBP->WidgetTree;
	UWidget* CanvasPanel = WidgetTree->ConstructWidget<UWidget>(WidgetClass, *WidgetName);

	return CanvasPanel;
}

void UAutoPSDUILibrary::SetWBPRootWidget(UWidgetBlueprint* ParentWBP, UWidget* Widget)
{
	UWidgetTree* WidgetTree = ParentWBP->WidgetTree;
	WidgetTree->RootWidget = Widget;
}

void UAutoPSDUILibrary::CompileAndSaveBP(UBlueprint* BPObject)
{
	FKismetEditorUtilities::CompileBlueprint(BPObject);
	UEditorAssetLibrary::SaveLoadedAsset(BPObject);
}

bool UAutoPSDUILibrary::ApplyInterfaceToBP(UBlueprint* BPObject, UClass* InterfaceClass)
{
	TArray<struct FBPInterfaceDescription> InterfaceDescription;
	FBPInterfaceDescription Description;
	Description.Interface = InterfaceClass;

	InterfaceDescription.Add(Description);
	BPObject->ImplementedInterfaces = InterfaceDescription;
	return true;
}

TSubclassOf<UObject> UAutoPSDUILibrary::GetBPGeneratedClass(UBlueprint* BPObject)
{
	return BPObject->GeneratedClass;
}
