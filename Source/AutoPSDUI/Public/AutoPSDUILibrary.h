// Copyright 2018-2021 - John snow wind
#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AutoPSDUILibrary.generated.h"

class UWidget;
class UWidgetBlueprint;


UCLASS()
class AUTOPSDUI_API UAutoPSDUILibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static void RunPyCmd(const FString& PyCmd);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static UObject* ImportImage(const FString& SrcFile, const FString& AssetPath);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static UWidgetBlueprint* CreateWBP(const FString& Asset);
	
	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static UWidget* MakeWidgetWithWBP(UClass* WidgetClass, UWidgetBlueprint* ParentWBP, const FString& WidgetName);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static void SetWBPRootWidget(UWidgetBlueprint* ParentWBP, UWidget* Widget);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static void CompileAndSaveBP(UBlueprint* BPObject);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static bool ApplyInterfaceToBP(UBlueprint* BPObject, UClass* InterfaceClass);

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUILibrary")
	static TSubclassOf<UObject> GetBPGeneratedClass(UBlueprint* BPObject);

};
