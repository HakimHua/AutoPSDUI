// Copyright 2018-2021 - John snow wind
#pragma once
#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "AutoPSDUISetting.generated.h"

struct FDirectoryPath;
class UFont;

UCLASS(config = Editor, defaultconfig)
class AUTOPSDUI_API UAutoPSDUISetting : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UAutoPSDUISetting();

	/* Whether enabled when import PSD file. */
	UPROPERTY(EditAnywhere, config, BlueprintReadWrite, Category = "AutoPSDUISetting")
	bool bEnabled;

	/* Source UI Texture Directory */
	UPROPERTY(EditAnywhere, config, BlueprintReadWrite, Category = "AutoPSDUISetting")
	FDirectoryPath TextureSrcDir;

	/* UI Texture Asset Directory */
	UPROPERTY(EditAnywhere, config, BlueprintReadWrite, Category = "AutoPSDUISetting", meta=(LongPackageName))
	FDirectoryPath TextureAssetDir;

	/* Font Map */
	UPROPERTY(EditAnywhere, config, BlueprintReadWrite, Category = "AutoPSDUISetting", meta = (LongPackageName))
	TMap<FString, TSoftObjectPtr<UFont>> FontMap;

	/* Default Map that font not found in font map*/
	UPROPERTY(EditAnywhere, config, BlueprintReadWrite, Category = "AutoPSDUISetting", meta = (LongPackageName))
	TSoftObjectPtr<UFont> DefaultFont;

	UFUNCTION(BlueprintCallable, Category = "AutoPSDUISetting")
	static UAutoPSDUISetting* Get();
};